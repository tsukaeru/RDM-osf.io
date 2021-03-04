'use strict';
// widget用ファイル

var $ = require('jquery');
var ko = require('knockout');
var Raven = require('raven-js');
var osfHelpers = require('js/osfHelpers');

var logPrefix = '[integromat] ';

require('./integromat.css');


function IntegromatWidget() {
    var self = this;
    self.baseUrl = window.contextVars.node.urls.api + 'integromat/';
    self.loading = ko.observable(true);
    self.loadFailed = ko.observable(false);
    self.loadCompleted = ko.observable(false);
    self.param_1 = ko.observable('');

    self.loadConfig = function() {
        var url = self.baseUrl + 'get_meetings';
        console.log(logPrefix, 'loading: ', url);

        return $.ajax({
            url: url,
            type: 'GET',
            dataType: 'json'
        }).done(function (data) {
            console.log(logPrefix, 'loaded: ', data);
            self.loading(false);
            self.loadCompleted(true);
            var meetingsJson = JSON.stringify(data);
            var meetings = JSON.parse(meetingsJson)
            self.param_1(meetings);
        }).fail(function(xhr, status, error) {
            self.loading(false);
            self.loadFailed(true);
            Raven.captureMessage('Error while retrieving addon info', {
                extra: {
                    url: url,
                    status: status,
                    error: error
                }
            });
        });
    };

}

var w = new IntegromatWidget();
osfHelpers.applyBindings(w, '#integromat-content');
w.loadConfig();
