/* Copyright 2022 donimuzur (<https://github.com/donimuzur>)
 * License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl). */

 odoo.define('pdfimage_viewer', function (require) {
    var relational_fields = require('web.relational_fields');
    var DocumentViewer = require('mail.DocumentViewer');
    var core = require('web.core');
    var FieldMany2ManyBinaryMultiFiles = relational_fields.FieldMany2ManyBinaryMultiFiles;
    
    var _t = core._t;
    var _lt = core._lt;
    var qweb = core.qweb;

    FieldMany2ManyBinaryMultiFiles.include({
        template_files: "FieldBinaryFileUploader2.files",
        
        events: _.extend({}, FieldMany2ManyBinaryMultiFiles.prototype.events, {
            'click .o_external_link': '_onClickTag',
        }),
    
        _onClickTag: function(event){
            event.preventDefault();
	        event.stopPropagation();
	        var self = this;
	        
            
            try {
                fileid = event.currentTarget.getAttribute('fileid');
            
                console.log(fileid);
                
                var file_mimetype = event.currentTarget.getAttribute('mimetype');

                function file_docView(file_data) {
                    if (file_data) {
                        var match = file_data.type.match("(image|video|application/pdf|text)");
                        if(match){
                            var file_attachment = [{
                                filename: file_data.name,
                                id: file_data.id,
                                is_main: false,
                                mimetype: file_data.type,
                                name: file_data.name,
                                type: file_data.type,
                                url: "/web/content/" + file_data.id + "?download=true",
                            }]
                            var file_activeAttachmentID = file_data.id;
                            var file_attachmentViewer = new DocumentViewer(self,file_attachment,file_activeAttachmentID);
                            file_attachmentViewer.appendTo($('body'));
                        }
                        else{
                            alert('This file type can not be previewed.')
                        }
                    }
                }
                if (file_mimetype) {
                    file_data = {
                        'id': event.currentTarget.getAttribute('fileid'),
                        'type': event.currentTarget.getAttribute('mimetype') || 'application/octet-stream',
                        'name': event.currentTarget.getAttribute('name') || event.currentTarget.getAttribute('display_name') || "",
                    }
                    file_docView(file_data);
                } else {
                    var def = ajax.jsonRpc("/get/record/details", 'call', {
                        'res_id': self.res_id,
                        'model': self.model,
                        'size': self.value,
                        'res_field': self.name || self.field.string,
                    });
                    return $.when(def).then(function(vals) {
                        if (vals && vals.id) {
                            file_docView(vals);
                        } else {
                            alert('The preview of the file can not be generated as it does not exist in the Odoo file system (Attachments).')
                        }
                    });
                }
            } catch (err) {
                alert(err);
            }
        },

        _generatedMetadata: function () {
            var self = this;
            _.each(this.value.data, function (record) {
                // tagging `allowUnlink` ascertains if the attachment was user
                // uploaded or was an existing or system generated attachment
                self.metadata[record.id] = {
                    id:record.id,
                    allowUnlink: self.uploadedFiles[record.data.id] || false,
                    url: self._getFileUrl(record.data),
                };
            });
        },

        _render: function () {
            // render the attachments ; as the attachments will changes after each
            // _setValue, we put the rendering here to ensure they will be updated
            this._generatedMetadata();
            this.$('.oe_placeholder_files, .oe_attachments')
                .replaceWith($(qweb.render(this.template_files, {
                    widget: this,
                })));
            this.$('.oe_fileupload').show();

            // display image thumbnail
            this.$('.o_image[data-mimetype^="image"]').each(function () {
                var $img = $(this);
                if (/gif|jpe|jpg|png/.test($img.data('mimetype')) && $img.data('src')) {
                    $img.css('background-image', "url('" + $img.data('src') + "')");
                }
            });
        },

        _render: function () {
            var self = this;
            self._super.apply(this, arguments);
        },
        
    });    
});