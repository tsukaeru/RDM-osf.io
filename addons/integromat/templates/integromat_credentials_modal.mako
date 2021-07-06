<div id="integromatCredentialsModal" class="modal fade">
    <div class="modal-dialog modal-lg">
        <div class="modal-content">

            <div class="modal-header">
                <h3>Connect an Integromat Account</h3>
            </div>

            <form>
                <div class="modal-body">

                    <div class="row">
                        <div class="col-sm-6">
                            <div class="form-group">
                                <label for="apiToken">API Token</label>
                                    <!-- Link to API token generation page -->
                                    <a href="https://apidocs.integromat.com/"
                                       target="_blank" class="text-muted addon-external-link">
                                        (Get from Integromat <i class="fa fa-external-link-square"></i>)
                                    </a>
                                <input class="form-control" data-bind="value: integromatApiToken" id="integromat_api_token" name="integromat_Api_Token" />
                            </div>
                        </div>
                    </div><!-- end row -->

                    <!-- Flashed Messages -->
                    <div class="help-block">
                        <p data-bind="html: message, attr: {class: messageClass}"></p>
                    </div>

                </div><!-- end modal-body -->

                <div class="modal-footer">

                    <a href="#" class="btn btn-default" data-bind="click: clearModal" data-dismiss="modal">Cancel</a>

                    <!-- Save Button -->
                    <button data-bind="click: connectAccount" class="btn btn-success">Save</button>

                </div><!-- end modal-footer -->

            </form>

        </div><!-- end modal-content -->
    </div>
</div>

<div id="manageWebMeetingAppsAttendeesModal" class="modal fade">
    <div class="modal-dialog">
        <div class="modal-content">

            <div class="modal-header">
                <h3>Manage Web Meeting Apps Attendees</h3>
            </div>
            <div class="modal-body">
                <div id="manageWebMeetingAttendees">

                    <ul class="nav nav-tabs">
                        <li class="active"><a data-bind="click: showAddAttendees">Add</a></li>
                        <li><a data-bind="click: showDeleteAttendees">Delete</a></li>
                    </ul>
                </div>

                <div id="addWebMeetingAttendees">
                    <form>
                        <div>
                            <label>User Guid</label>
                            <input type="text" data-bind="value: userGuid">
                        </div>
                        <div>
                            <label style="padding-top: 10px;">Microsoft Teams</label>
                        </div>
                        <div style="padding-left: 25px;">
                            <label>Sign-in Address</label>
                            <input type="text" data-bind="value: microsoftTeamsMail">
                        </div>
                        <div style="padding-left: 25px;">
                            <label>User Name</label>
                            <input type="text" data-bind="value: microsoftTeamsUserName">
                        </div>
                        <div style="padding-top: 10px;">
                            <label>Webex Meetings</label>
                        </div>
                        <div style="padding-left: 25px;">
                            <label>Sign-in Address</label>
                            <input type="text" data-bind="value: webexMeetingsMail">
                        </div>
                        <div style="padding-left: 25px;">
                            <label>Display Name</label>
                            <input type="text" data-bind="value: webexMeetingsDisplayName">
                        </div>
                    </form>
                    <!-- Flashed Messages -->
                    <div class="help-block">
                        <p data-bind="html: message, attr: {class: messageClass}"></p>
                    </div>
                    <div>
                        <button data-bind="click: addWebMeetingAppsUser" style="margin-top:5px; margin-bottom:5px;" class="btn btn-success pull-right">Add</button>
                    </div>
                    
                </div>

            <div id="deleteWebMeetingAttendees">
                <form>
                    <div>
                        <label>User Guid</label>
                        <input type="text" data-bind="value: userGuidToDelete">
                    </div>
                </form>
                <!-- Flashed Messages -->
                <div class="help-block">
                    <p data-bind="html: message, attr: {class: messageClass}"></p>
                </div>
                <div>
                    <button data-bind="click: deleteMicrosoftTeamsUser" style="margin-top:5px; margin-bottom:5px;" class="btn btn-danger pull-right">Delete</button>
                </div>
            </div>
            </div><!-- end modal-body -->
        </div><!-- end modal-content -->
    </div>
</div>