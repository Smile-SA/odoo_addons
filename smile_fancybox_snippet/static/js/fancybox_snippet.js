odoo.define('smile_fancybox_snippet.fancybox_snippet', function (require) {
'use strict';

    var core = require('web.core');
    var Dialog = require('web.Dialog');
    var weWidgets = require('wysiwyg.widgets');
    var options = require('web_editor.snippets.options');

    var _t = core._t;
    var qweb = core.qweb;

    options.registry.fancybox = options.Class.extend({

        /**
         * Taken from Odoo Image Gallery Snippet
         */
        start: function () {
            var self = this;

            // The snippet should not be editable
            this.$target.attr('contentEditable', false);

            // Make sure image previews are updated if images are changed
            this.$target.on('save', 'img', function (ev) {
                var $img = $(ev.currentTarget);
                var index = self.$target.find('.carousel-item.active').index();
            });

            this.$target.on('click', '.o_add_images', function (e) {
                e.stopImmediatePropagation();
                self.addImages(false);
            });

            return this._super.apply(this, arguments);
        },

        addImages: function (previewMode) {
            var self = this;
            var $row = $('<div/>', {class: 'row'});
            var $container = this.$('.container:first');
            var imgs = this._getImages();
            var dialog = new weWidgets.MediaDialog(this, {multiImages: true, onlyImages: true, mediaWidth: 1920});
            var lastImage = _.last(imgs);
            var index = lastImage ? this._getIndex(lastImage) : -1;

            dialog.on('save', this, function (attachments) {
                for (var i = 0 ; i < attachments.length; i++) {
                    var $col = $('<div/>', {class: 'col-md-4'});
                    var $img = $('<a/>', {
                        class: 'truesize_img',
                        href: attachments[i].image_src,
                        'data-fancybox': 'gallery',
                        'data-index': ++index,
                    }).append($('<img/>', {
                                class: 'thumbnail_group',
                                src: attachments[i].image_src,}));
                    $col.append($img);
                    $col.append($('<br/>'));
                    $col.append($('<br/>'));
                    $row.append($col);
                    if ((index + 1) % 3 === 0){
                        $row = $('<div/>', {class: 'row'});
                        $container.append($row);
                    }
                }
                self._reset();
                self.trigger_up('cover_update');
                this._setActive();
            });
            dialog.open();
            this._replaceContent($row);
        },

        removeAllImages: function (previewMode) {
            var $addImg = $('<div>', {
                class: 'alert alert-info css_editable_mode_display text-center',
            });
            var $text = $('<span>', {
                class: 'o_add_images',
                style: 'cursor: pointer;',
                text: _t(" Add Images"),
            });
            var $icon = $('<i>', {
                class: ' fa fa-plus-circle',
            });
            this._replaceContent($addImg.append($icon).append($text));
        },

        _replaceContent: function ($content) {
            var $container = this.$('.container:first');
            $container.empty().append($content);
            return $container;
        },

        _getIndex: function (img) {
            return img.dataset.index || 0;
        },

        _getImages: function () {
            var imgs = this.$('img').get();
            var self = this;
            imgs.sort(function (a, b) {
                return self._getIndex(a) - self._getIndex(b);
            });
            return imgs;
        },
    });
});
