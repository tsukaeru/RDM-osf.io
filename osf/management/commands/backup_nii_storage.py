# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import datetime as dt
import os
import json
import csv
import zipfile

from django.db import connection
from django.core.management.base import BaseCommand

from addons.osfstorage.models import OsfStorageFileNode
from osf.models import (
    Institution,
    ProjectStorageType,
    AbstractNode,
    OSFUser,
    Guid
)


FILE_INFO_SELECT_SQL = """
        SELECT 
          ob.id,
          ob.type,
          ob.name,
          ob.parent_id,
          ob.target_object_id,
          ob.is_root,
          of.size,
          of.metadata,
          of.creator_id,
          of.modified,
          of.location,
          of.identifier
        FROM osf_basefilenode as ob
         LEFT JOIN osf_basefileversionsthrough AS obf
             ON (ob.id = obf.basefilenode_id AND ob.type = 'osf.osfstoragefile')
         LEFT JOIN osf_fileversion AS of
             ON (of.id = obf.fileversion_id)
         WHERE ob.id IN  ( %s )
         ORDER BY ob.id, of.identifier

    """

# CSV file header info
header = [
    'project name',
    'project GUID',
    'file path',
    'file name',
    'file name(sha256)',
    'file GUID',
    'file size(byte)',
    'file version',
    'modified date(JST)',
    'file creator(GUID)'
]

# Output NII storage project info
def export_osf_data(institution_name, backup_files_path):

    print('---- Start output NII storage project info----')
    institution = Institution.objects.filter(name=institution_name).values('id')
    # get user affiliated institution id
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
                    print('project_storage_type_id :{}'.format(projectstoragetypeid))
                    projectstoragetype = AbstractNode.objects.filter(projectstoragetype__id=projectstoragetypeid['projectstoragetype'])
                    storage_type = ProjectStorageType.objects.get(node=projectstoragetype).storage_type
                    print('storage_type_cd :{}'.format(storage_type))

                    # NII STORAGE
                    if storage_type == ProjectStorageType.NII_STORAGE:
                        print('----The NII Storage----')
                        targetobjectid = projectstoragetype.filter(type='osf.node').values_list('id', flat=True)[0]
                        # get the osf_basefilenode.target_object_id
                        print("osf_basefilenode.target_object_id:{}".format(targetobjectid))

                        # get project guid
                        project_guid = Guid.objects.filter(object_id=targetobjectid, content_type_id=4).values('_id')[0]['_id']
                        print('project guid :{}'.format(project_guid))

                        # get project name
                        project_name = user.nodes.exclude(is_deleted=True).filter(type='osf.node', id=targetobjectid).values('title')[0]['title']
                        print('project_name :{}'.format(project_name))

                        project_info = OsfStorageFileNode.objects.filter(
                           target_object_id=targetobjectid
                        )
                        print(project_info)
                        print('project_info.count :{}'.format(project_info.count()))
                        print(project_info.filter(name=''))

                        # get project files id
                        files_ids = project_info.values_list('id', flat=True)
                        print(files_ids)

                        # get files info
                        fileinfo = get_file_info(files_ids)
                        print(fileinfo)
                        for rowdata in fileinfo:
                            file_path = ''
                            file_guid = ''
                            if rowdata[1] == 'osf.osfstoragefile':

                                fileguiddata = Guid.objects.filter(object_id=rowdata[0], content_type_id=91).values('_id')
                                if fileguiddata.count() > 0:
                                    file_guid = fileguiddata[0]['_id']
                                    print('file_guid :{}'.format(file_guid))

                                file_name = rowdata[2]
                                print('file_name :{}'.format(file_name))

                                file_path = get_file_path(fileinfo, rowdata, targetobjectid, file_path)
                                print('file_path :{}'.format(file_path))

                                file_size = rowdata[6]
                                print('file_size :{}'.format(file_size))

                                sha256_file_name = get_json_value(rowdata[7], "sha256")
                                print('sha256_file_name :{}'.format(sha256_file_name))

                                modified_date = rowdata[9]
                                print('modified_date :{}'.format(modified_date))

                                creator_guid = Guid.objects.filter(object_id=rowdata[8], content_type_id=1).values('_id')[0]['_id']
                                print('creator_guid :{}'.format(creator_guid))

                                file_version = rowdata[11]
                                print('file_version :{}'.format(file_version))

                                csv_writer.writerow([project_name, project_guid, file_path, file_name, sha256_file_name,
                                                     file_guid, file_size, file_version, modified_date, creator_guid])

                                # add resource file to zip
                                osffilepath = get_json_value(rowdata[10], "folder")
                                print('osf_resource_file_path :{}'.format(osffilepath))
                                fullpath = osffilepath + '/' + sha256_file_name
                                if os.path.exists(fullpath):
                                    print('zip_write_resource_file :{}'.format(fullpath))
                                    osffilezip.write(fullpath)

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

    print('---- End output NII storage project info----')


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


# get files info
def get_file_info(files_ids):

    with connection.cursor() as cursor:
        # output osf_basefileversionsthrough.json file
        format_strings = ','.join(['%s'] * len(files_ids))
        cursor.execute(FILE_INFO_SELECT_SQL % format_strings, tuple(files_ids))
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
        export_osf_data(
            institution_name=options['institution_name'],
            backup_files_path=options['backup_files_path'],
        )
