# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import datetime as dt
import os
import json
import csv
import zipfile

from django.db import connection
from django.core.management.base import BaseCommand
from pytz import timezone

from osf.models import (
    Institution,
    ProjectStorageType,
    AbstractNode,
    OSFUser,
    Guid
)

# get google drive external storage info
GOOGlE_DRIVE_EXTERNAL_STORAGE_SELECT_SQL = """
        SELECT 
          addons_googledrive_nodesettings.folder_id,
          addons_googledrive_nodesettings.modified,
          osf_externalaccount.provider
        FROM osf_externalaccount
          INNER JOIN osf_osfuser_external_accounts 
            ON osf_externalaccount.id = osf_osfuser_external_accounts.externalaccount_id
          INNER JOIN addons_googledrive_nodesettings 
            ON osf_externalaccount.id = addons_googledrive_nodesettings.external_account_id
                AND addons_googledrive_nodesettings.owner_id = %s
        WHERE osf_osfuser_external_accounts.osfuser_id = %s
          AND (osf_externalaccount.provider = 'googledrive' OR osf_externalaccount.provider = 'googledriveinstitutions')

    """

# CSV file header info
header = [
    'project name' ,
    'project GUID' ,
    'folder ID', 
    'modified date(JST)' ,
    'storage creator(GUID)',
    'external storage short name'
]

# Output external storage project info
def export_external_data(institution_name, backup_files_path):

    print('---- Start output external storage project info----')
    institution = Institution.objects.filter(name=institution_name).values('id')
    institution_id = institution[0]['id']
    print('institution_id :{}'.format(institution_id))

    for user in OSFUser.objects.all():
        if user.affiliated_institutions.exists():
            if user.affiliated_institutions.filter(pk=institution_id).exists():
                osfusers=user.affiliated_institutions.filter(pk=institution_id).values('osfuser')
                # osf_osfuser.id
                osfuserid = osfusers[0]['osfuser']
                print('osfuser_id: {}'.format(osfuserid))

                osfuser_guid = Guid.objects.filter(object_id=osfuserid, content_type_id=1).values('_id')[0]['_id']
                print('osfuser_guid: {}'.format(osfuser_guid))

                # creat csv file
                strDate = "{0:%Y%m%d}".format(dt.datetime.now())
                filename = institution_name.replace(" ", "") + "_" + osfuser_guid + "_" + strDate
                csvfilename = filename + ".csv"
                csvfilename = filename + ".csv"
                print('out_put_csv_file_name: {}'.format(csvfilename))
                folder_name_exist = os.path.exists(backup_files_path)
                if not folder_name_exist:
                    os.makedirs(backup_files_path)
                print(os.path.exists(backup_files_path + "/" + csvfilename))

                csvfile = open(backup_files_path + "/" + csvfilename, 'w', encoding='utf-8')
                csv_writer = csv.writer(csvfile)
                csv_writer.writerow(header)
                print(os.path.exists(backup_files_path + "/" + csvfilename))

                osffilezip = zipfile.ZipFile(filename + '.zip','w')

                # get osf_projectstoragetype.id (osf_abstractnode.id=osf_projectstoragetype.node_id)
                projectstoragetypeids = user.nodes.exclude(is_deleted=True).filter(type='osf.node').values('projectstoragetype')
                for projectstoragetypeid in projectstoragetypeids:
                    print('project_storagetype_id :{}'.format(projectstoragetypeid))
                    projectstoragetype = AbstractNode.objects.filter(projectstoragetype__id=projectstoragetypeid['projectstoragetype'])
                    storage_type = ProjectStorageType.objects.get(node=projectstoragetype).storage_type
                    print('storage_type_cd :{}'.format(storage_type))

                    targetobjectid = projectstoragetype.filter(type='osf.node').values_list('id', flat=True)[0]
                    # get the osf_basefilenode.target_object_id
                    print("osf_basefilenode.target_object_id:{}".format(targetobjectid))

                    # get project guid
                    project_guid = Guid.objects.filter(object_id=targetobjectid, content_type_id=4).values('_id')[0]['_id']
                    print('project guid :{}'.format(project_guid))

                    # get project name
                    project_name = user.nodes.exclude(is_deleted=True).filter(type='osf.node', id=targetobjectid).values('title')[0]['title']
                    print('project_name :{}'.format(project_name))


                    # get files info
                    external_storage_info = get_external_storage_info(GOOGlE_DRIVE_EXTERNAL_STORAGE_SELECT_SQL, [targetobjectid, osfuserid])
                    print(external_storage_info)
                    print(len(external_storage_info))
                    if len(external_storage_info) > 0:
                        csv_writer.writerow([project_name, project_guid, external_storage_info[0][0],
                                             external_storage_info[0][1].astimezone(timezone('Asia/Tokyo')) , osfuser_guid, external_storage_info[0][2]])

                osffilezip.write(backup_files_path + "/" + csvfilename)

                print('----zip file test begin-------------------')
                infos = osffilezip.infolist()

                for info in infos:
                    print(info.filename)
                print( osffilezip.read(info.filename) )
                print('----zip file test end-------------------')


                print('----csv file test begin-------------------')
                csvfile = open(backup_files_path + "/" + csvfilename, 'r+', encoding='utf-8')
                read_csv = csv.reader(csvfile)
                for csvdata in read_csv:
                    print(csvdata)
                print('----csv file test end-------------------')

    print('---- End output external storage project info----')


# get file path
def get_file_path(fileinfo, rowdata, targetobjectid, file_path):
    
    parent_id = rowdata[3]
    if parent_id == targetobjectid:
        return ''

    for data in fileinfo: 
        if data[1] == 'osf.osfstoragefolder' and data[0] == parent_id:
            file_path = data[2] + '/' + file_path
            if data[3] == targetobjectid:
                return file_path
            else:
                get_file_path(fileinfo, data, targetobjectid, file_path)

# get json value
def get_json_value(jsondata, itmename):
    arraydata = json.dumps(jsondata)
    json_dict = json.loads(arraydata)
    return json_dict[itmename]


# get external storage info
def get_external_storage_info(select_sql, argArray):

    with connection.cursor() as cursor:
        cursor.execute(select_sql, argArray)
        return cursor.fetchall()


class Command(BaseCommand):

    def add_arguments(self, parser):

        super(Command, self).add_arguments(parser)
        parser.add_argument(
            '--institution_name',
            type=str,
            required=True,
            help='Input the Institution name.'
        )

        parser.add_argument(
            '--backup_files_path',
            type=str,
            required=True,
            help='Input the backup files path.'
        )

    def handle(self, *args, **options):
        export_external_data(
            institution_name=options['institution_name'],
            backup_files_path=options['backup_files_path'],
        )
