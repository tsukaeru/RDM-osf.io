'use strict';

var ko = require('knockout');
var $ = require('jquery');
var Raven = require('raven-js');
var osfHelpers = require('js/osfHelpers');
var oop = require('js/oop');
var m = require('mithril');
var bootbox = require('bootbox');
var $osf = require('js/osfHelpers');
var OauthAddonFolderPicker = require('js/oauthAddonNodeConfig')._OauthAddonNodeConfigViewModel;

var IntegromatFolderPickerViewModel = oop.extend(OauthAddonFolderPicker, {
    constructor: function(addonName, url, selector, folderPicker, opts, tbOpts) {
        var self = this;
        self.super.constructor(addonName, url, selector, folderPicker, tbOpts);
        // Non-OAuth fields
        self.integromatApiToken = ko.observable();
        self.integromatWebhookUrl = ko.observable();
        self.userGuid = ko.observable();
        self.microsoftTeamsUserObject = ko.observable();
        self.microsoftTeamsMail = ko.observable();
        self.userGuidToDelete = ko.observable();
        // Treebeard config
        self.treebeardOptions = $.extend(
            {},
            OauthAddonFolderPicker.prototype.treebeardOptions,
            {   // TreeBeard Options
                columnTitles: function() {
                    return [{
                        title: 'Buckets',
                        width: '75%',
                        sort: false
                    }, {
                        title: 'Select',
                        width: '25%',
                        sort: false
                    }];
                },
                resolveToggle: function(item) {
                    return '';
                },
                resolveIcon: function(item) {
                    return m('i.fa.fa-folder-o', ' ');
                },
            },
            tbOpts
        );
    },

    connectAccount: function() {
        var self = this;
        if (!self.integromatApiToken() ){
            self.changeMessage('Please enter an API token.', 'text-danger');
            return;
        }
        if (!self.integromatWebhookUrl() ){
            self.changeMessage('Please enter an Webhook URL.', 'text-danger');
            return;
        }
        $osf.block();

        return $osf.postJSON(
            self.urls().create, {
                integromat_api_token: self.integromatApiToken(),
                integromat_webhook_url: self.integromatWebhookUrl()
            }
        ).done(function(response) {
            $osf.unblock();
            self.clearModal();
            $('#integromatCredentialsModal').modal('hide');
            self.changeMessage('Successfully added Integromat credentials.', 'text-success', null, true);
            self.updateFromData(response);
            self.importAuth();
        }).fail(function(xhr, status, error) {
            $osf.unblock();
            var message = '';
            var response = JSON.parse(xhr.responseText);
            if (response && response.message) {
                message = response.message;
            }
            self.changeMessage(message, 'text-danger');
            Raven.captureMessage('Could not add Integromat credentials', {
                extra: {
                    url: self.urls().importAuth,
                    textStatus: status,
                    error: error
                }
            });
        });
    },
    /**
     * Tests if the given string is a valid Integromat bucket name.  Supports two modes: strict and lax.
     * Strict is for bucket creation and follows the guidelines at:
     *
     *   http://docs.aws.amazon.com/AmazonS3/latest/dev/BucketRestrictions.html#bucketnamingrules
     *
     * However, the US East (N. Virginia) region currently permits much laxer naming rules.  The S3
     * docs claim this will be changed at some point, but to support our user's already existing
     * buckets, we provide the lax mode checking.
     *
     * Strict checking is the default.
     *
     * @param {String} bucketName user-provided name of bucket to validate
     * @param {Boolean} laxChecking whether to use the more permissive validation
     */
    isValidBucketName: function(bucketName, laxChecking) {
        if (laxChecking === true) {
            return /^[a-zA-Z0-9.\-_]{1,255}$/.test(bucketName);
        }
        var label = '[a-z0-9]+(?:[a-z0-9\-]*[a-z0-9])?';
        var strictBucketName = new RegExp('^' + label + '(?:\\.' + label + ')*$');
        var isIpAddress = /^[0-9]+(?:\.[0-9]+){3}$/;
        return bucketName.length >= 3 && bucketName.length <= 63 &&
            strictBucketName.test(bucketName) && !isIpAddress.test(bucketName);
    },

    /** Reset all fields from Integromat credentials input modal */
    clearModal: function() {
        var self = this;
        self.message('');
        self.messageClass('text-info');
        self.integromatApiToken(null);
        self.integromatWebhookUrl(null);
    },

    createBucket: function(self, bucketName) {
        $osf.block();
        bucketName = bucketName.toLowerCase();
        return $osf.postJSON(
            self.urls().createBucket, {bucket_name: bucketName}
        ).done(function(response) {
            $osf.unblock();
            self.loadedFolders(false);
            self.activatePicker();
            var msg = 'Successfully created bucket "' + $osf.htmlEscape(bucketName) + '". You can now select it from the list.';
            var msgType = 'text-success';
            self.changeMessage(msg, msgType, null, true);
        }).fail(function(xhr) {
            var resp = JSON.parse(xhr.responseText);
            var message = resp.message;
            var title = resp.title || 'Problem creating bucket';
            $osf.unblock();
            if (!message) {
                message = 'Looks like that name is taken. Try another name?';
            }
            bootbox.confirm({
                title: $osf.htmlEscape(title),
                message: $osf.htmlEscape(message),
                callback: function(result) {
                    if (result) {
                        self.openCreateBucket();
                    }
                },
                buttons:{
                    confirm:{
                        label:'Try again'
                    }
                }
            });
        });
    },

    openCreateBucket: function() {
        var self = this;

        bootbox.dialog({
            title: 'Create a new bucket',
            message:
                    '<div class="row"> ' +
                        '<div class="col-md-12"> ' +
                            '<form class="form-horizontal" onsubmit="return false"> ' +
                                '<div class="form-group"> ' +
                                    '<label class="col-md-4 control-label" for="bucketName">Bucket Name</label> ' +
                                    '<div class="col-md-8"> ' +
                                        '<input id="bucketName" name="bucketName" type="text" placeholder="Enter bucket name" class="form-control" autofocus> ' +
                                        '<div>' +
                                            '<span id="bucketModalErrorMessage" ></span>' +
                                        '</div>'+
                                    '</div>' +
                                '</div>' +
                            '</form>' +
                        '</div>' +
                    '</div>',
            buttons: {
                cancel: {
                    label: 'Cancel',
                    className: 'btn-default'
                },
                confirm: {
                    label: 'Create',
                    className: 'btn-success',
                    callback: function () {
                        var bucketName = $('#bucketName').val();

                        if (!bucketName) {
                            var errorMessage = $('#bucketModalErrorMessage');
                            errorMessage.text('Bucket name cannot be empty');
                            errorMessage[0].classList.add('text-danger');
                            return false;
                        } else if (!self.isValidBucketName(bucketName, false)) {
                            bootbox.confirm({
                                title: 'Invalid bucket name',
                                message: 'Integromat buckets can contain lowercase letters, numbers, and hyphens separated by' +
                                ' periods.  Please try another name.',
                                callback: function (result) {
                                    if (result) {
                                        self.openCreateBucket();
                                    }
                                },
                                buttons: {
                                    confirm: {
                                        label: 'Try again'
                                    }
                                }
                            });
                        } else {
                            self.createBucket(self, bucketName);
                        }
                    }
                }
            }
        });
    },

    addMicrosoftTeamsUser : function() {
        var self = this;
        if (!self.userGuid() ){
            self.changeMessage('Please enter an User guid.', 'text-danger');
            return;
        }
        if (!self.microsoftTeamsMail() ){
            self.changeMessage('Please enter an Microsoft Teams Sign-in Address.', 'text-danger');
            return;
        }

        if (!self.microsoftTeamsUserObject() ){
            self.changeMessage('Please enter an Microsoft Teams User Object ID.', 'text-danger');
            return;
        }

        var url = self.urls().add_microsoft_teams_user;
        return osfHelpers.postJSON(
            url,
            ko.toJS({
                user_guid: self.userGuid(),
                microsoft_teams_user_object: self.microsoftTeamsUserObject(),
                microsoft_teams_mail: self.microsoftTeamsMail()
            })
        ).done(function() {
            self.message('');
            $('#microsoftTeamsUserRegistrationModal').modal('hide');
            self.userGuid(null);
            self.microsoftTeamsUserObject(null);
            self.microsoftTeamsMail(null);
            self.userGuidToDelete(null);

        }).fail(function(xhr, textStatus, error) {
            var errorMessage = (xhr.status === 401) ? '401' : 'Duplicate';
            self.changeMessage(errorMessage, 'text-danger');
            Raven.captureMessage('Could not add Micorosoft Teams user', {
                url: self.url,
                textStatus: textStatus,
                error: error
            });
        });
    },

    deleteMicrosoftTeamsUser : function() {
        var self = this;
        if (!self.userGuidToDelete() ){
            self.changeMessage('Please enter an User guid for Delete.', 'text-danger');
            return;
        }
        var url = self.urls().delete_microsoft_teams_user;
        return osfHelpers.postJSON(
            url,
            ko.toJS({
                user_guid: self.userGuidToDelete(),
            })
        ).done(function() {
            self.message('');
            $('#microsoftTeamsUserRegistrationModal').modal('hide');
            self.userGuid(null);
            self.microsoftTeamsUserObject(null);
            self.microsoftTeamsMail(null);
            self.userGuidToDelete(null);

        }).fail(function(xhr, textStatus, error) {
            var errorMessage = (xhr.status === 401) ? '401' : 'Error';
            self.changeMessage(errorMessage, 'text-danger');
            Raven.captureMessage('Could not delete Micorosoft Teams user', {
                url: self.url,
                textStatus: textStatus,
                error: error
            });
        });
    }

});

// Public API
function IntegromatNodeConfig(addonName, selector, url, folderPicker, opts, tbOpts) {
    var self = this;
    self.url = url;
    self.folderPicker = folderPicker;
    opts = opts || {};
    tbOpts = tbOpts || {};
    self.viewModel = new IntegromatFolderPickerViewModel(addonName, url, selector, folderPicker, opts, tbOpts);
    self.viewModel.updateFromData();
    $osf.applyBindings(self.viewModel, selector);
}

module.exports = {
    IntegromatNodeConfig: IntegromatNodeConfig,
    _IntegromatNodeConfigViewModel: IntegromatFolderPickerViewModel
};
