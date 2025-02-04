<%inherit file="project/project_base.mako"/>
<%def name="title()">${node['title']} ${_("Settings")}</%def>

<div class="page-header visible-xs">
  <h2 class="text-300">${_("Settings")}</h2>
</div>
<div class="row project-page">
    <!-- Begin left column -->
    <div class="col-md-3 col-xs-12 affix-parent scrollspy">

        % if permissions.WRITE in user['permissions']:

            <div class="panel panel-default osf-affix" data-spy="affix" data-offset-top="0" data-offset-bottom="263"><!-- Begin sidebar -->
                <ul class="nav nav-stacked nav-pills">

                    % if not node['is_registration']:
                        <li><a href="#configureNodeAnchor">${_(node['node_type'].capitalize())}</a></li>
                    % endif

                    % if storage_flag_is_active:
                        <li><a href="#nodeStorageLocation">${_("Storage Location")}</a></li>
                    % endif

                    % if not node['is_registration']:
                        % if permissions.ADMIN in user['permissions']:
                            % if not use_viewonlylinks:
                            <div style="display: none;">
                            % endif
                            <li><a href="#createVolsAnchor">${_("View-only Links")}</a></li>
                            % if not use_viewonlylinks:
                            </div>
                            % endif
                            <li><a href="#enableRequestAccessAnchor">${_("Access Requests")}</a></li>
                        % endif

                        <li><a href="#configureWikiAnchor">${_("Wiki")}</a></li>

                        % if use_project_comment_settings:
                        % if permissions.ADMIN in user['permissions']:
                            <li><a href="#configureCommentingAnchor">${_("Commenting")}</a></li>
                        % endif
                        % endif

                        <li><a href="#configureNotificationsAnchor">${_("Email Notifications")}</a></li>

                        <li><a href="#redirectLink">${_("Redirect Link")}</a></li>

                    % endif

                    % if node['is_registration']:

                        % if (node['is_public'] or node['embargo_end_date']) and permissions.ADMIN in user['permissions']:
                            <li><a href="#withdrawRegistrationAnchor">${_("Withdraw Public Registration")}</a></li>
                        % endif

                    % endif

                    % if enable_institutions and use_project_institution_settings:
                        <li><a href="#configureInstitutionAnchor">${_("Project Affiliation / Branding")}</a></li>
                    % endif

                </ul>
            </div><!-- End sidebar -->
        % endif

    </div>
    <!-- End left column -->

    <!-- Begin right column -->
    <div class="col-md-9 col-xs-12">

        % if permissions.WRITE in user['permissions']:  ## Begin Configure Project

            % if not node['is_registration']:
                <div class="panel panel-default">
                    <span id="configureNodeAnchor" class="anchor"></span>
                    <div class="panel-heading clearfix">
                        <h3 id="configureNode" class="panel-title">${_(node['node_type'].capitalize())}</h3>
                    </div>

                    <div id="projectSettings" class="panel-body">
                        <div class="form-group">
                            <label for="category">${_("Category:")}</label>
                            <i>${_("(For descriptive purposes)")}</i>
                            <div class="dropdown generic-dropdown category-list">
                                <button class="btn btn-default dropdown-toggle" type="button" data-toggle="dropdown">
                                    <span data-bind="getIcon: selectedCategory"></span>
                                    <span data-bind="text: selectedCategoryLabel" class="text-capitalize"></span>
                                    <span data-bind="ifnot: selectedCategory">${_("Uncategorized")}</span>
                                    <i class="fa fa-sort"></i>
                                </button>
                                <ul class="dropdown-menu" data-bind="foreach: {data: categoryOptions, as: 'category'}">
                                    <li>
                                          <a href="#" data-bind="click: $root.setCategory.bind($root, category.value)">
                                              <span data-bind="getIcon: category.value"></span>
                                              <span data-bind="text: category.label"></span>
                                          </a>
                                    </li>
                                </ul>
                            </div>
                        </div>
                        <div class="form-group">
                            <label for="title">${_("Title:")}</label>
                            <input class="form-control" type="text" maxlength="200" placeholder="Required" data-bind="value: title,
                                                                                                      valueUpdate: 'afterkeydown'">
                            <span class="text-danger" data-bind="validationMessage: title"></span>
                        </div>
                        <div class="form-group">
                            <label for="description">${_("Description:")}</label>
                            <textarea placeholder="${_('Optional')}" data-bind="value: description,
                                             valueUpdate: 'afterkeydown'",
                            class="form-control resize-vertical" style="max-width: 100%"></textarea>
                        </div>
                    % if 'admin' in user['permissions'] and 0:
                        <div class="form-group">
                            <label for="description">${_("Select Timestamp Function:")}</label>
                            <select id="timestamp_pattern" data-bind="value: selectedTimestampPattern">
                            % if timestamp_pattern_division == 1:
                                 <option value="1" selected>${_("Timestamp only")}</option>
<%doc> Only "Timestamp only" (while digital signature develop)
                                 <option value="2">${_("Timestamp with digital signature")}</option>
</%doc>
                            % else:
                                 <option value="1">${_("Timestamp only")}</option>
<%doc>
                                 <option value="2" selected>${_("Timestamp with digital signature")}</option>
</%doc>
                            % endif
                            </select>
                        </div>
                    % endif
                           <button data-bind="click: cancelAll"
                            class="btn btn-default">${_("Cancel")}</button>
                            <button data-bind="click: updateAll"
                            class="btn btn-success">${_("Save changes")}</button>
                        <div class="help-block">
                            <span data-bind="css: messageClass, html: message"></span>
                        </div>
                    % if permissions.ADMIN in user['permissions']:
                        <hr />
                        % if can_delete:
                            <div class="help-block">
                                ${_("A project cannot be deleted if it has any components within it.\
                                To delete a parent project, you must first delete all child components\
                                by visiting their settings pages.")}
                            </div>
                            <span data-bind="stopBinding: true">
                                <span id="deleteNode">
                                    <button
                                    data-toggle="modal" data-target="#nodesDelete"
                                    data-bind="click: $root.delete.bind($root, ${node['child_exists'] | sjson, n}, '${node['node_type']}', ${node['is_supplemental_project'] | sjson, n}, '${node['api_url']}')"
                                    class="btn btn-danger btn-delete-node">${_("Delete %(nodeType)s") % dict(nodeType=_(node['node_type']))}</button>
                                    <%include file="project/nodes_delete.mako"/>
                                </span>
                            </span>
                        % else:
                            <div class="help-block">
                                ${_("A project which is related to a external group (%(group)s) cannot be deleted.") % dict(group=group)}
                            </div>
                            <span data-bind="stopBinding: true">
                                <span id="deleteNode">
                                    <button disabled="disabled"
                                    data-toggle="modal" data-target="#nodesDelete"
                                    data-bind="click: $root.delete.bind($root, ${node['child_exists'] | sjson, n}, '${node['node_type']}', ${node['is_preprint'] | sjson, n}, '${node['api_url']}')"
                                    class="btn btn-danger btn-delete-node">${_("Delete %(nodeType)s") % dict(nodeType=_(node['node_type']))}</button>
                                    <%include file="project/nodes_delete.mako"/>
                                </span>
                            </span>
                       % endif
                    % endif
                    </div>
                </div>

            % endif

        % if storage_flag_is_active:
            <div class="panel panel-default">
                <span id="nodeStorageLocation" class="anchor"></span>
                <div class="panel-heading clearfix">
                    <h3 id="nodeStorageLocation" class="panel-title">${_("Storage Location")}</h3>
                </div>
                <div class="panel-body">
                    <p>
                        <b>Storage location:</b> ${node['storage_location']}
                    </p>
                    <div class="help-block">
                        <p class="text-muted">${_("Storage location cannot be changed after project is created.")}</p>
                    </div>

                </div>
            </div>
        % endif

        % endif  ## End Configure Project

        % if permissions.ADMIN in user['permissions']:  ## Begin create VOLS
            % if not node['is_registration']:
              % if not use_viewonlylinks:
                <div style="display: none;">
              % endif
                <div class="panel panel-default">
                    <span id="createVolsAnchor" class="anchor"></span>
                    <div class="panel-heading clearfix">
                        <h3 class="panel-title">${_("View-only Links")}</h3>
                    </div>
                    <div class="panel-body">
                        <p>
                            ${_("Create a link to share this project so those who have the link can view&mdash;but not edit&mdash;the project.")}
                        </p>
                        <a href="#addPrivateLink" data-toggle="modal" class="btn btn-success btn-sm">
                          <i class="fa fa-plus"></i> ${_("Add")}
                        </a>
                        <%include file="project/private_links.mako"/>
                    </div>
                </div>
              % if not use_viewonlylinks:
                </div>
              % endif
            % endif
        % endif ## End create vols

        % if permissions.ADMIN in user['permissions']:  ## Begin enable request access
            % if not node['is_registration']:
                <div class="panel panel-default">
                    <span id="enableRequestAccessAnchor" class="anchor"></span>
                    <div class="panel-heading clearfix">
                        <h3 class="panel-title">${_("Access Requests")}</h3>
                    </div>
                    <div class="panel-body">
                        <form id="enableRequestAccessForm">
                            <div>
                                <label class="break-word">
                                    <input
                                            type="checkbox"
                                            name="projectAccess"
                                            class="project-access-select"
                                            data-bind="checked: enabled"
                                    />
                                    ${_("Allow users to request access to this project.")}
                                </label>
                                <div data-bind="visible: enabled()" class="text-success" style="padding-left: 15px">
                                    <p data-bind="text: requestAccessMessage"></p>
                                </div>
                                <div data-bind="visible: !enabled()" class="text-danger" style="padding-left: 15px">
                                    <p data-bind="text: requestAccessMessage"></p>
                                </div>
                            </div>
                        </form>
                    </div>
                </div>
            % endif
        % endif ## End enable request access

        % if permissions.WRITE in user['permissions']:  ## Begin Wiki Config
            % if not node['is_registration']:
                <div class="panel panel-default">
                    <span id="configureWikiAnchor" class="anchor"></span>
                    <div class="panel-heading clearfix">
                        <h3 class="panel-title">${_("Wiki")}</h3>
                    </div>

                <div class="panel-body">
                        <form id="selectWikiForm">
                            <div>
                                <label class="break-word">
                                    <input
                                            type="checkbox"
                                            name="wiki"
                                            class="wiki-select"
                                            data-bind="checked: enabled"
                                    />
                                    ${_("Enable the wiki in <b>%(title)s</b>.") % dict(title=h(node['title'])) | n}
                                </label>

                                <div data-bind="visible: enabled()" class="text-success" style="padding-left: 15px">
                                    <p data-bind="text: wikiMessage"></p>
                                </div>
                                <div data-bind="visible: !enabled()" class="text-danger" style="padding-left: 15px">
                                    <p data-bind="text: wikiMessage"></p>
                                </div>
                            </div>
                        </form>

                        %if wiki_enabled:
                            <h3>${_("Configure")}</h3>
                            <div style="padding-left: 15px">
                                %if node['is_public']:
                                    <p class="text">${_("Control who can edit the wiki of <b>%(title)s</b>") % dict(title=h(node['title'])) | n}</p>
                                %else:
                                    <p class="text">${_("Control who can edit your wiki")}</p>
                                %endif
                            </div>

                            <form id="wikiSettings" class="osf-treebeard-minimal">
                                <div id="wgrid">
                                    <div class="spinner-loading-wrapper">
                                        <div class="ball-scale ball-scale-blue">
                                            <div></div>
                                        </div>
                                        <p class="m-t-sm fg-load-message"> ${_("Loading wiki settings...")}  </p>
                                    </div>
                                </div>
                                <div class="help-block" style="padding-left: 15px">
                                    <p id="configureWikiMessage"></p>
                                </div>
                            </form>
                        %endif
                    </div>
                </div>
            %endif
        %endif ## End Wiki Config

        % if use_project_comment_settings:
        % if permissions.ADMIN in user['permissions']:  ## Begin Configure Commenting

            % if not node['is_registration']:

                <div class="panel panel-default">
                    <span id="configureCommentingAnchor" class="anchor"></span>
                    <div class="panel-heading clearfix">
                        <h3 class="panel-title">${_("Commenting")}</h3>
                    </div>

                    <div class="panel-body">

                        <form class="form" id="commentSettings">

                            <div class="radio">
                                <label>
                                    <input type="radio" name="commentLevel" value="private" ${'checked' if comments['level'] == 'private' else ''}>
                                    ${_("Only contributors can post comments")}
                                </label>
                            </div>
                            <div class="radio">
                                <label>
                                    <input type="radio" name="commentLevel" value="public" ${'checked' if comments['level'] == 'public' else ''}>
                                    ${_("When the %(nodeType)s is public, any GakuNin RDM user can post comments") % dict(nodeType=_(h(node['node_type'])))}
                                </label>
                            </div>

                            <button class="btn btn-success">${_("Save")}</button>

                            <!-- Flashed Messages -->
                            <div class="help-block">
                                <p id="configureCommentingMessage"></p>
                            </div>
                        </form>

                    </div>

                </div>
                %endif
            % endif  ## End Configure Commenting
        % endif

        % if user['has_read_permissions']:  ## Begin Configure Email Notifications

            % if not node['is_registration']:

                <div class="panel panel-default">
                    <span id="configureNotificationsAnchor" class="anchor"></span>
                    <div class="panel-heading clearfix">
                        <h3 class="panel-title">${_("Email Notifications")}</h3>
                    </div>
                    <div class="panel-body">
                        <div class="help-block">
                            <p class="text-muted">${_("These notification settings only apply to you. They do NOT affect any other contributor on this project.")}</p>
                        </div>
                        <form id="notificationSettings" class="osf-treebeard-minimal">
                            <div id="grid">
                                <div class="spinner-loading-wrapper">
                                    <div class="ball-scale ball-scale-blue">
                                        <div></div>
                                    </div>
                                    <p class="m-t-sm fg-load-message"> ${_("Loading notification settings...")}  </p>
                                </div>
                            </div>
                            <div class="help-block" style="padding-left: 15px">
                                <p id="configureNotificationsMessage"></p>
                            </div>
                        </form>
                    </div>
                </div>

            %endif

        % endif ## End Configure Email Notifications

        % if permissions.WRITE in user['permissions']:  ## Begin Redirect Link Config
            % if not node['is_registration']:

                <div class="panel panel-default">
                    <span id="redirectLink" class="anchor"></span>
                    <div class="panel-heading clearfix">
                        <h3 class="panel-title">${_("Redirect Link")}</h3>
                    </div>
                    <div class="panel-body" id="configureForward">
                        <div>
                            <label>
                                <input
                                    type="checkbox"
                                    name="forward"
                                    data-bind="checked: enabled, disable: pendingRequest"
                                    ${'disabled' if node['is_registration'] else ''}
                                />
                                ${_("Redirect visitors from your project page to an external webpage")}
                            </label>
                        </div>

                        <div data-bind="visible: enabled" style="display: none">

                            ${ render_node_settings(addon_settings['forward']) }

                        </div><!-- end #configureForward -->

                    </div>
                </div>
            %endif
        %endif ## End Redirect Link Config

        % if permissions.ADMIN in user['permissions']:  ## Begin Retract Registration

            % if node['is_registration']:

                % if node['is_public'] or node['is_embargoed']:

                    <div class="panel panel-default">
                        <span id="withdrawRegistrationAnchor" class="anchor"></span>

                        <div class="panel-heading clearfix">
                            <h3 class="panel-title">${_("Withdraw Registration")}</h3>
                        </div>

                        <div class="panel-body">

                            % if parent_node['exists']:

                                <div class="help-block">
                                  ${_('Withdrawing children components of a registration is not allowed. Should you wish to\
                                  withdraw this component, please withdraw its parent registration <a %(webUrlFor)s>here</a>.') % dict(href='href="' + h(webUrlFor=web_url_for('node_setting', pid=node['root_id'])) + '"') | n}
                                </div>

                            % else:

                                <div class="help-block">
                                    ${_("Withdrawing a registration will remove its content from the GakuNin RDM, but leave basic metadata\
                                    behind. The title of a withdrawn registration and its contributor list will remain, as will\
                                    justification or explanation of the withdrawal, should you wish to provide it. Withdrawn\
                                    registrations will be marked with a <strong>withdrawn</strong> tag.") | n}
                                </div>

                                %if not node['is_pending_retraction']:
                                    <a class="btn btn-danger" href="${web_url_for('node_registration_retraction_get', pid=node['id'])}">${_("Withdraw Registration")}</a>
                                % else:
                                    <p><strong>${_("This registration is already pending withdrawal.")}</strong></p>
                                %endif

                            % endif

                        </div>
                    </div>

                % endif

            % endif

        % endif  ## End Retract Registration

        % if enable_institutions and use_project_institution_settings:
             <div class="panel panel-default scripted" id="institutionSettings">
                 <span id="configureInstitutionAnchor" class="anchor"></span>
                 <div class="panel-heading clearfix">
                     <h3 class="panel-title">${_("Project Affiliation / Branding")}</h3>
                 </div>
                 <div class="panel-body">
                     <div class="help-block">
                         % if permissions.WRITE not in user['permissions']:
                             <p class="text-muted">${_("Contributors with read-only permissions to this project cannot add or remove institutional affiliations.")}</p>
                         % endif:
                         <!-- ko if: affiliatedInstitutions().length == 0 -->
                         ${_("Projects can be affiliated with institutions that have created GakuNin RDM for Institutions accounts.")}
                         ${_("This allows:")}
                         <ul>
                            <li>${_("institutional logos to be displayed on public projects")}</li>
                            <li>${_("public projects to be discoverable on specific institutional landing pages")}</li>
                            <li>${_("single sign-on to the GakuNin RDM with institutional credentials")}</li>
                            <li><a href="https://openscience.zendesk.com/hc/en-us/categories/360001550913">${_("FAQ")}</a></li>
                         </ul>
                         <!-- /ko -->
                     </div>
                     <!-- ko if: affiliatedInstitutions().length > 0 -->
                     <label>${_("Affiliated Institutions:")} </label>
                     <!-- /ko -->
                     <table class="table">
                         <tbody>
                             <!-- ko foreach: {data: affiliatedInstitutions, as: 'item'} -->
                             <tr>
                                 <td><img class="img-circle" width="50px" height="50px" data-bind="attr: {src: item.logo_path_rounded_corners}"></td>
                                 <td><span data-bind="text: item.name"></span></td>
                                 <td>
                                     % if permissions.ADMIN in user['permissions']:
                                         <button data-bind="disable: $parent.loading(), click: $parent.clearInst" class="pull-right btn btn-danger">${_("Remove")}</button>
                                     % elif permissions.WRITE in user['permissions']:
                                         <!-- ko if: $parent.userInstitutionsIds.indexOf(item.id) !== -1 -->
                                            <button data-bind="disable: $parent.loading(), click: $parent.clearInst" class="pull-right btn btn-danger">${_("Remove")}</button>
                                         <!-- /ko -->
                                     % endif
                                 </td>
                             </tr>
                             <!-- /ko -->
                         </tbody>
                     </table>
                         </br>
                     <!-- ko if: availableInstitutions().length > 0 -->
                     <label>${_("Available Institutions:")} </label>
                     <table class="table">
                         <tbody>
                             <!-- ko foreach: {data: availableInstitutions, as: 'item'} -->
                             <tr>
                                 <td><img class="img-circle" width="50px" height="50px" data-bind="attr: {src: item.logo_path_rounded_corners}"></td>
                                 <td><span data-bind="text: item.name"></span></td>
                                 % if permissions.WRITE in user['permissions']:
                                     <td><button
                                             data-bind="disable: $parent.loading(),
                                             click: $parent.submitInst"
                                             class="pull-right btn btn-success">${_("Add")}</button></td>
                                 % endif
                             </tr>
                             <!-- /ko -->
                         </tbody>
                     </table>
                     <!-- /ko -->
                 </div>
            </div>
        % endif

    </div>
    <!-- End right column -->

</div>

<%def name="render_node_settings(data)">
    <%
       template_name = data['node_settings_template']
       tpl = data['template_lookup'].get_template(template_name).render(**data)
    %>
    ${ tpl | n }
</%def>

<%def name="stylesheets()">
    ${parent.stylesheets()}
    <link rel="stylesheet" href="/static/css/pages/project-page.css">
    <link rel="stylesheet" href="/static/css/responsive-tables.css">
</%def>

<%def name="javascript_bottom()">
    ${parent.javascript_bottom()}
    <script>
      window.contextVars = window.contextVars || {};
      window.contextVars.node = window.contextVars.node || {};
      window.contextVars.node.description = ${node['description'] | sjson, n };
      window.contextVars.node.nodeType = ${ node['node_type'] | sjson, n };
      window.contextVars.node.isSupplementalProject = ${ node['is_supplemental_project'] | sjson, n };
      window.contextVars.node.institutions = ${ node['institutions'] | sjson, n };
      window.contextVars.node.requestProjectAccessEnabled = ${node['access_requests_enabled'] | sjson, n };
      window.contextVars.nodeCategories = ${ categories | sjson, n };
      window.contextVars.wiki = window.contextVars.wiki || {};
      window.contextVars.wiki.isEnabled = ${wiki_enabled | sjson, n };
      window.contextVars.currentUser = window.contextVars.currentUser || {};
      window.contextVars.currentUser.institutions = ${ user['institutions'] | sjson, n };
      window.contextVars.currentUser.permissions = ${ user['permissions'] | sjson, n } ;
      window.contextVars.timestampPattern = ${ node['timestamp_pattern_division'] | sjson, n };
      window.contextVars.analyticsMeta = $.extend(true, {}, window.contextVars.analyticsMeta, {
          pageMeta: {
              title: 'Settings',
              pubic: false,
          },
      });
    </script>

    <script type="text/javascript" src=${"/static/public/js/project-settings-page.js" | webpack_asset}></script>
    <script src=${"/static/public/js/sharing-page.js" | webpack_asset}></script>

    % if not node['is_registration']:
        <script type="text/javascript" src=${"/static/public/js/forward/node-cfg.js" | webpack_asset}></script>
    % endif


</%def>
