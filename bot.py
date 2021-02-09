import os
import confs
import requests
from vk_api import VkApi
from vk_api import VkUpload

class Base(object):

    __slots__ = ('config')

    def __init__(self,password: str):
        self.config = confs.Config('password')
        if not self.has_sync_chat():
            self.new_sync_chat()
        print('Syncing remote files...')
        print('Current Config: ', self.config.data)
        self.config.data['sync_files'] = self.get_attachments_from(self.config.data['sync_chat'])
        self.config.data['sync_files'].reverse()
        print('Remote files synced')
        self.save()

    def get_attachments_from(self, archive_id: int):
        # todo: получать больше 200ста файлов
        attachs = self.config.api.messages.getHistoryAttachments(peer_id=archive_id,media_type='doc',count=200)['items']
        attach_json = []
        for attach in attachs:
            title = attach['attachment']['doc']['title']
            link = attach['attachment']['doc']['url']
            message_id = attach['message_id']
            attach_json.append({'title':title, 'link':link, 'debug_id':message_id})
        return attach_json

    def has_sync_chat(self) -> bool:
        if not self.config.data['sync_chat']:
            return False
        return True

    def new_sync_chat(self) -> None:
        print('Доступные архивы:')
        for a, name in list(enumerate(self.config.data['archives'])):
            print(a, name['name'])
        chat_id = int(input('Выберите чат для синхронизации: '))
        self.config.data['sync_chat'] = self.config.data['archives'][chat_id]['id']
        self.sync_remote_archive_title()

    def upload_file(self, path_to_file: str):
        up = VkUpload(self.config.api)
        filename = os.path.basename(path_to_file)
        new_uploaded_file = up.document(doc = path_to_file,title=filename)
        return new_uploaded_file['doc']['owner_id'], new_uploaded_file['doc']['id']

    def delete_temp_file(self, owner_id: str, file_id: str):
        self.config.api.docs.delete(owner_id=owner_id, doc_id=file_id)

    def upload_file_to_archive(self, path_to_file: str, archive_id = None):
        if not archive_id:
            owner_id, file_id = self.upload_file(path_to_file)
            attach = 'doc' + str(owner_id) + '_' + str(file_id)
            self.config.api.messages.send(peer_id = self.config.data['sync_chat'], attachment=attach, random_id = 0)
        self.delete_temp_file(owner_id,file_id)

    def delete_files_from_archive(self):
        print('DELMODE: Выберите файлы, которые вы хотите удалить (eg. "0 3 5")')
        for i, data in enumerate(self.config.data['sync_files']):
            print(i, data['title'])
        queue = list(map(int, input().split()))
        # todo: проверка на выход за приделы массива

        message_ids = ''
        for file_n in queue:
            message_ids += str(self.config.data['sync_files'][file_n]['debug_id']) + ','
        message_ids = message_ids[:-1]

        # todo: добавить время загрузки файлов чтобы сразу определять можно ли "удалить для всех"
        self.config.api.messages.delete(message_ids=message_ids,delete_for_all=0)
        self.config.data['sync_files'] = self.get_attachments_from(self.config.data['sync_chat'])
        print('Файлы удалены!')

    def sync_remote_archive_title(self):
        chat_id = int(self.config.data['sync_chat']) - confs.PEER_CONST
        remote_title = self.config.api.messages.getChat(chat_id=chat_id)['title']
        # todo: conflicts
        self.config.data['sync_chat_title'] = remote_title

    def download_file(self,url: str, place: str) -> None:
        r = requests.get(url)
        with open(place, 'wb') as f:
            f.write(r.content)

    def save(self):
        self.config.save_in_file()

Base('123')
