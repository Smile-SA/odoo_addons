# -*- coding: utf-8 -*-
# © 2016 Therp BV <http://therp.nl>
# © 2017 ThinkOpen Solutions <https://tkobr.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import logging
import os
import shutil
import subprocess
import tempfile
import threading
import time

import odoo
from odoo.tests import common

ADMIN_USER_ID = common.ADMIN_USER_ID

from odoo import api, fields, models, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)
_MARKER_PHRASE = '[[waiting for OCR]]'
_PDF_OCR_DOCUMENTS_THREADS = []
OCR_LANGUAGE = [('afr', 'Afrikaans'),
                ('amh', 'Amharic'),
                ('ara', 'Arabic'),
                ('asm', 'Assamese'),
                ('aze', 'Azerbaijani'),
                ('aze_cyrl', 'Azerbaijani - Cyrilic'),
                ('bel', 'Belarusian'),
                ('ben', 'Bengali'),
                ('bod', 'Tibetan'),
                ('bos', 'Bosnian'),
                ('bul', 'Bulgarian'),
                ('cat', 'Catalan; Valencian'),
                ('ceb', 'Cebuano'),
                ('ces', 'Czech'),
                ('chi_sim', 'Chinese - Simplified'),
                ('chi_tra', 'Chinese - Traditional'),
                ('chr', 'Cherokee'),
                ('cym', 'Welsh'),
                ('dan', 'Danish'),
                ('dan_frak', 'Danish - Fraktur'),
                ('deu', 'German'),
                ('deu_frak', 'German - Fraktur'),
                ('dzo', 'Dzongkha'),
                ('ell', 'Greek, Modern (1453-)'),
                ('eng', 'English'),
                ('enm', 'English, Middle (1100-1500)'),
                ('epo', 'Esperanto'),
                ('equ', 'Math / equation detection module'),
                ('est', 'Estonian'),
                ('eus', 'Basque'),
                ('fas', 'Persian'),
                ('fin', 'Finnish'),
                ('fra', 'French'),
                ('frk', 'Frankish'),
                ('frm', 'French, Middle (ca.1400-1600)'),
                ('gle', 'Irish'),
                ('glg', 'Galician'),
                ('grc', 'Greek, Ancient (to 1453)'),
                ('guj', 'Gujarati'),
                ('hat', 'Haitian; Haitian Creole'),
                ('heb', 'Hebrew'),
                ('hin', 'Hindi'),
                ('hrv', 'Croatian'),
                ('hun', 'Hungarian'),
                ('iku', 'Inuktitut'),
                ('ind', 'Indonesian'),
                ('isl', 'Icelandic'),
                ('ita', 'Italian'),
                ('ita_old', 'Italian - Old'),
                ('jav', 'Javanese'),
                ('jpn', 'Japanese'),
                ('kan', 'Kannada'),
                ('kat', 'Georgian'),
                ('kat_old', 'Georgian - Old'),
                ('kaz', 'Kazakh'),
                ('khm', 'Central Khmer'),
                ('kir', 'Kirghiz; Kyrgyz'),
                ('kor', 'Korean'),
                ('kur', 'Kurdish'),
                ('lao', 'Lao'),
                ('lat', 'Latin'),
                ('lav', 'Latvian'),
                ('lit', 'Lithuanian'),
                ('mal', 'Malayalam'),
                ('mar', 'Marathi'),
                ('mkd', 'Macedonian'),
                ('mlt', 'Maltese'),
                ('msa', 'Malay'),
                ('mya', 'Burmese'),
                ('nep', 'Nepali'),
                ('nld', 'Dutch; Flemish'),
                ('nor', 'Norwegian'),
                ('ori', 'Oriya'),
                ('osd', 'Orientation and script detection module'),
                ('pan', 'Panjabi; Punjabi'),
                ('pol', 'Polish'),
                ('por', 'Portuguese'),
                ('pus', 'Pushto; Pashto'),
                ('ron', 'Romanian; Moldavian; Moldovan'),
                ('rus', 'Russian'),
                ('san', 'Sanskrit'),
                ('sin', 'Sinhala; Sinhalese'),
                ('slk', 'Slovak'),
                ('slk_frak', 'Slovak - Fraktur'),
                ('slv', 'Slovenian'),
                ('spa', 'Spanish; Castilian'),
                ('spa_old', 'Spanish; Castilian - Old'),
                ('sqi', 'Albanian'),
                ('srp', 'Serbian'),
                ('srp_latn', 'Serbian - Latin'),
                ('swa', 'Swahili'),
                ('swe', 'Swedish'),
                ('syr', 'Syriac'),
                ('tam', 'Tamil'),
                ('tel', 'Telugu'),
                ('tgk', 'Tajik'),
                ('tgl', 'Tagalog'),
                ('tha', 'Thai'),
                ('tir', 'Tigrinya'),
                ('tur', 'Turkish'),
                ('uig', 'Uighur; Uyghur'),
                ('ukr', 'Ukrainian'),
                ('urd', 'Urdu'),
                ('uzb', 'Uzbek'),
                ('uzb_cyrl', 'Uzbek - Cyrilic'),
                ('vie', 'Vietnamese'),
                ('yid', 'Yiddish'), ]


def ncpus():
    # for Linux, Unix and MacOS
    if hasattr(os, "sysconf"):
        if os.sysconf_names.has_key("SC_NPROCESSORS_ONLN"):
            # Linux and Unix
            ncpus = os.sysconf("SC_NPROCESSORS_ONLN")
            if isinstance(ncpus, int) and ncpus > 0:
                return ncpus
        else:
            # MacOS X
            return int(os.popen2("sysctl -n hw.ncpu")[1].read())
    # for Windows
    if os.environ.has_key("NUMBER_OF_PROCESSORS"):
        ncpus = int(os.environ["NUMBER_OF_PROCESSORS"])
        if ncpus > 0:
            return ncpus
    # return the default value
    return 1


_SEMAPHORES_POOL = threading.BoundedSemaphore(ncpus())


class IrAttachment(models.Model):
    _inherit = 'ir.attachment'

    language = fields.Selection(OCR_LANGUAGE, 'Language',
                                default=lambda self:
                                self.env['ir.config_parameter'].get_param(
                                    'document_ocr.language', 'eng'))
    # We need to redefine index_content field to be able to update it
    # on the onchange_language() in form
    index_content = fields.Text('Indexed Content',
                                readonly=False,
                                prefetch=False)
    index_content_rel = fields.Text(related='index_content',
                                    string='Indexed Content Rel')
    processing_time = fields.Char('Processing Time',
                                  readonly=True,
                                  copy=False,
                                  help='Processing time.\n'
                                       '(00:00:00 means less than one second)')

    @api.onchange('language')
    def onchange_language(self):
        process = subprocess.Popen(['tesseract', '--list-langs'],
                                   stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE)
        stdout, stderr = process.communicate()
        if self.language not in stderr.split('\n')[1:-1]:
            raise UserError(_(
                "Language not installed."
                " Please ask your system administrator to"
                " install tesseract '%s' language." %
                self.language))
        if self.store_fname:
            bin_data = self._file_read(self.store_fname)
        else:
            bin_data = self.db_datas
        if bin_data:
            index_content = self._index(
                bin_data.decode('base64'), self.datas_fname, self.mimetype)
            return {'value': {
                'index_content': index_content}}
        return {'value': {}}

    @api.model
    def _index(self, bin_data, datas_fname, mimetype):
        content = super(IrAttachment, self)._index(
            bin_data, datas_fname, mimetype)
        if not content or content == 'image':
            has_synchr_param = self.env['ir.config_parameter'].get_param(
                'document_ocr.synchronous', 'False') == 'True'
            has_force_flag = self.env.context.get('document_ocr_force')
            synchr = has_synchr_param or has_force_flag
            if synchr:
                content = self._index_ocr(bin_data)
            else:
                content = _MARKER_PHRASE
        return content

    def _index_ocr(self, bin_data):
        if self.datas_fname:
            process = subprocess.Popen(
                ['tesseract', 'stdin', 'stdout', '-l', self.language],
                stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            stdout, stderr = process.communicate(bin_data)
            if stderr:
                _logger.warning('Error during OCR: %s', stderr)
            return stdout
        else:
            _logger.warning('OCR IMAGE "%s", no image to process...',
                            self.name)
        return False

    def _ocr_image_thread(self, i, t, image):
        global ocr_images_text
        with _SEMAPHORES_POOL:
            with threading.Lock():
                _logger.info('OCR PDF INFO "%s" image %d/%d to text...',
                             self.name, i, t)
                ocr_images_text[self.id][i] = self._index_ocr(image)

    def _index_doc_pdf_thread(self, bin_data):
        global ocr_images_text
        ocr_images_text[self.id] = {}
        buf = _MARKER_PHRASE
        tmpdir = tempfile.mkdtemp()
        _logger.info('OCR PDF INFO "%s"...', self.name)
        time_start = time.time()
        stdout, stderr = subprocess.Popen(
            ['pdftotext', '-layout', '-nopgbrk', '-', '-'],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE).communicate(bin_data)
        if stderr:
            _logger.warning('OCR PDF ERROR to text: %s',
                            stderr)
        buf = stdout
        # OCR PDF Images
        stdout, stderr = subprocess.Popen(
            ['pdfimages', '-p', '-', tmpdir + '/ocr'],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE).communicate(bin_data)
        if stderr:
            _logger.warning('OCR PDF WARNING Images: %s',
                            stderr)
        # OCR every image greater than 50Kb
        filelist = sorted([(file) for file
                           in os.listdir(tmpdir)
                           if os.path.getsize(
                os.path.join(tmpdir, file)) > 50000])
        filelist_size = len(filelist)
        count = 1
        workers = []
        for pdf in filelist:
            img_file = os.path.join(tmpdir, pdf)
            image = open(img_file, 'rb').read()
            t = threading.Thread(target=self._ocr_image_thread,
                                 name=u'ocr_image_' + str(count),
                                 args=(count,
                                       filelist_size,
                                       image))
            t.start()
            count += 1
            workers.append(t)
        for t in workers:
            t.join()
        index_content = buf
        for text in sorted(ocr_images_text[self.id]):
            try:
                index_content = \
                    u'%s\n%s' % (
                        index_content,
                        ocr_images_text[self.id][text])
            except:
                try:
                    index_content = \
                        u'%s\n%s' % (
                            index_content,
                            ocr_images_text[self.id][text].decode(
                                'utf8'))
                except:
                    try:
                        index_content = \
                            u'%s\n%s' % (
                                index_content.decode('utf8'),
                                ocr_images_text[self.id][text])
                    except:
                        try:
                            index_content = \
                                u'%s\n%s' % (
                                    index_content.decode('utf8'),
                                    ocr_images_text[self.id][text].decode('utf8'))
                        except:
                            shutil.rmtree(tmpdir)
        ocr_images_text.pop(self.id)  # release memory
        m, s = divmod((time.time() - time_start), 60)
        h, m = divmod(m, 60)
        self.index_content = index_content
        self.processing_time = "%02d:%02d:%02d" % (h, m, s)
        shutil.rmtree(tmpdir)
        return self.index_content

    def _index_pdf(self, bin_data):
        global ocr_images_text
        buf = _MARKER_PHRASE
        has_synchr_param = self.env['ir.config_parameter'].get_param(
            'document_ocr.synchronous', 'False') == 'True'
        has_force_flag = self.env.context.get('document_ocr_force')
        synchr = has_synchr_param or has_force_flag
        try:
            if ocr_images_text:
                pass
        except:
            ocr_images_text = {}
        if synchr:
            buf = self._index_doc_pdf_thread(bin_data)
        else:
            buf = _MARKER_PHRASE
        return buf

    @api.model
    def _ocr_cron(self):
        for this in self.with_context(document_ocr_force=True).search(
                [('index_content', '=', _MARKER_PHRASE)]):
            if not this.datas:
                continue
            index_content = this._index(
                this.datas.decode('base64'), this.datas_fname, this.mimetype)
            this.write({
                'index_content': index_content,
            })