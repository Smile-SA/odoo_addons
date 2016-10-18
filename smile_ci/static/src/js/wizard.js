odoo.define('smile_ci.DownloadDockerImage', function (require) {
    'use strict';

    var core = require('web.core');
    var Widget = require('web.Widget');

    var DownloadDockerImageWizard = Widget.extend({
        template: 'download_docker_image_wizard',
        events: {
            'click button#button_copy': 'copy_to_clipboard',
            'click button#button_download': 'donwload_file',
        },
        init: function(parent, context) {
            this._super(parent, context);
            this.docker_registry_insecure = context.context.docker_registry_insecure;
            this.docker_registry_url = context.context.docker_registry_url;
            this.docker_registry_image = context.context.docker_registry_image;
            this.docker_tags = context.context.docker_tags;
            this.default_tag = context.context.default_tag;
            this.odoo_dir = context.context.odoo_dir;
            this.attachment_id = context.context.attachment_id;
        },
        copy_to_clipboard: function() {
            var target = $('#button_copy')[0].dataset.copyTarget,
                input = $(target);
            input.select();
            try {
                document.execCommand('copy');
                if (window.getSelection) { // IE >=9 and all other browsers
                    var selection = window.getSelection();
                    if (selection.removeAllRanges) {
                        selection.removeAllRanges();
                    } else if (selection.empty) {
                        selection.empty();
                    }
                } else if (document.selection) { // IE gt;9
                  document.selection.empty();
                } 
            } catch (err) {
                alert('Please press Ctrl/Cmd+C to copy');
            }
        },
        donwload_file: function() {
            window.open('/web/content/'  + this.attachment_id + '?download=true');
        },
    });

    core.action_registry.add('download_docker_image', DownloadDockerImageWizard);

    return DownloadDockerImageWizard;
});
