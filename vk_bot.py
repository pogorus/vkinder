from random import randrange
from datetime import datetime
import requests
import vk_api
from vk_api.longpoll import VkLongPoll, VkEventType

user_token = 'user token'
token = 'group token'

vk = vk_api.VkApi(token=token)
longpoll = VkLongPoll(vk)

class VkUser:
    def __init__(self, user_id, bdate, sex, city):
        self.user_id = user_id
        if len(bdate[0]) == 1:
            bdate[0] = f'0{bdate[0]}'
        if len(bdate[1]) == 1:
            bdate[1] = f'0{bdate[1]}'
        self.age = (int(datetime.today().strftime('%Y%m%d')) - int(''.join(bdate[::-1]))) // 10000
        self.sex = sex
        self.city = city
        self.counter = 0

counter = 0

def get_photo(id):
    response = requests.get('https://api.vk.com/method/photos.get',
                            params={'access_token': user_token, 'v': '5.131', 'album_id': 'profile',
                                    'extended': '1', 'owner_id': id}).json()

    photo_dict = {}
    for photo in response['response']['items']:
        photo_dict[photo['id']] = photo['likes']['count'] + photo['reposts']['count'] + photo['comments']['count']

    sorted_photo = sorted(photo_dict.items(), key=lambda item: item[1])
    return sorted_photo[-1:-4:-1]

def write_msg(user_id, message):
    vk.method('messages.send', {'user_id': user_id, 'message': message,  'random_id': randrange(10 ** 7)})

def send_attachment(user_id, owner_id, photo_id):
    vk.method('messages.send', {'user_id': user_id, 'message': '', 'attachment': f'photo{owner_id}_{photo_id}', 'random_id': randrange(10 ** 7)})

for event in longpoll.listen():
    if event.type == VkEventType.MESSAGE_NEW:

        if event.to_me:
            request = event.text
            user_id = event.user_id

            response = requests.get('https://api.vk.com/method/users.get',
                                    params={'access_token': token, 'v': '5.131', 'user_ids': request,
                                            'fields': 'city, sex, bdate'}).json()

            vk_id = response['response'][0]['id']
            try:
                bdate = response['response'][0]['bdate'].split('.')
            except KeyError:
                bdate = []
            try:
                sex = response['response'][0]['sex']
            except KeyError:
                sex = ''
            try:
                city = response['response'][0]['city']['id']
            except KeyError:
                city = ''

            if bdate == [] or len(bdate) < 3:
                write_msg(user_id, 'Укажите дату рождения в формате: дд.мм.гггг')
                for event in longpoll.listen():
                    if event.type == VkEventType.MESSAGE_NEW:

                        if event.to_me:
                            request = event.text
                            user_id = event.user_id
                            bdate = request.split('.')
                            break

            if sex == '':
                write_msg(user_id, 'Укажите пол: 1 - женский; 2 - мужской')
                for event in longpoll.listen():
                    if event.type == VkEventType.MESSAGE_NEW:

                        if event.to_me:
                            request = event.text
                            user_id = event.user_id
                            sex = request
                            break

            if city == '':
                write_msg(user_id, 'Укажите город')
                for event in longpoll.listen():
                    if event.type == VkEventType.MESSAGE_NEW:

                        if event.to_me:
                            request = event.text
                            user_id = event.user_id
                            city = request.lower()
                            city_response = requests.get('https://api.vk.com/method/database.getCities',
                                    params={'access_token': user_token, 'v': '5.131', 'country_id': 1,
                                            'q': city, 'need_all': '0', 'count': 1}).json()
                            city = city_response['response']['items'][0]['id']
                            break

            user = VkUser(vk_id, bdate, sex, city)

            search_response = requests.get('https://api.vk.com/method/users.search',
                                           params={'access_token': user_token, 'v': '5.131', 'sort': 0,
                                                   'sex': 1 if user.sex == 2 else 2,
                                                   'count': 1, 'status': 6, 'age_from': user.age,
                                                   'age_to': user.age, 'offset': counter,
                                                   'has_photo': 1, 'city': user.city, 'fields': 'id',
                                                   'is_closed': 0}).json()
            counter += 1

            if search_response['response']['items'] == [] or search_response['response']['items'][0]['is_closed']:
                while search_response['response']['items'] == [] or search_response['response']['items'][0]['is_closed']:
                    search_response = requests.get('https://api.vk.com/method/users.search',
                                                   params={'access_token': user_token, 'v': '5.131', 'sort': 0,
                                                           'sex': 1 if user.sex == 2 else 2,
                                                           'count': 1, 'status': 6, 'age_from': user.age,
                                                           'age_to': user.age, 'offset': counter,
                                                           'has_photo': 1, 'city': user.city, 'fields': 'id',
                                                           'is_closed': 0}).json()
                    counter += 1

            write_msg(user_id, f'https://vk.com/id{search_response["response"]["items"][0]["id"]}')

            photos = get_photo(search_response['response']['items'][0]['id'])

            for photo in photos:
                send_attachment(user_id, search_response['response']['items'][0]['id'], photo[0])

