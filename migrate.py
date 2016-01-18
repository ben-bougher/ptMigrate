import requests
import json
import urllib
from PIL import Image
import cStringIO
import tempfile

"""
Class for migrating data to the new PickThis
"""

dummy_password = "new_user"


def data_from_url(url):

    im = Image.open(cStringIO.StringIO(urllib.urlopen(url).read()))

    temp = tempfile.NamedTemporaryFile(prefix='tmp', suffix='.png')
    im.save(temp)
    return({"file": open(temp.name, 'rb')})


def convert_interps(data):

    new_data = [[]]

    for pick in data:

        if len(pick) == 2:
            point = dict(x=pick[0], y=pick[1])
            new_data[0].append(point)

        else:
            point = dict(x=pick[0], y=pick[1])
            interp = pick[2]
            while interp >= len(new_data):
                new_data.append([])
            new_data[interp].append(point)
            
    return new_data


class PTMigrate(object):

    def __init__(self, old_api, new_api, user_file=None):

        self.old_api = old_api
        self.new_api = new_api

        # Lookup table for old and new user ids
        self.user_map = {}

        if user_file:
            
            with open(user_file, 'r') as f:
                self.user_map = json.load(f)

    def migrate_users(self, mapfile='user_map.json'):
        """
        Mimics migration by manually registering every user in the old
        database. Writes a mapping of pt_old user ids to pt_new user_ids
        to a json file mapfile
        """

        dummy_password = 'new_user'
        get_url = "{api}/api/users?all=1".format(api=self.old_api)
        user_data = requests.get(get_url).json()

        for user in user_data:

            try:
                create_user_url = "{api}/register".format(api=self.new_api)
                reg = requests.put(create_user_url,
                                   json={"email": user["email"],
                                         "password": dummy_password,
                                         "callback_url": "dummy"})

                reg_data = reg.json()
                verify_url = "{api}/verified/{user_id}".format(api=self.new_api,
                                                               user_id=reg_data["id"])
                
                user_data = requests.post(verify_url)
                self.user_map[user["user_id"]] = user_data.json()["id"]

                print("Success: ", user["user_id"])

            except Exception as e:
                print("FAILURE: ", user["user_id"])

                print(e)

        with open(mapfile, 'w') as f:
            json.dump(self.user_map, f)
        
    def migrate_images(self):
        """
        The old app uses the image as the base for the whole experiment.
        The new app treats it as an independent entity.
        
        For all the images from the new app log in as the user,
        upload the image, then redefine the new experiment. Get all
        the picks and again replay them for each user and add them.
        """

        image_url = "{api}/api/images?all=1".format(api=self.old_api)
        image_data = requests.get(image_url)

        for image in image_data.json():

            try:
                new_user_id = self.user_map[image["user"]]

                upload_url = "{api}/upload_image".format(api=self.new_api)
                new_image = requests.post(upload_url,
                                          files=data_from_url(image["link"]),
                                          auth=(new_user_id, dummy_password)).json()

                meta = dict(rights=image["permission"],
                            rights_owner=image["rightsholder"],
                            description=image["description"])

                update_url = "{api}/image/{image_id}".format(api=self.new_api,
                                                             image_id=new_image["id"])

                requests.put(update_url,
                             json=meta,
                             auth=(new_user_id, dummy_password))

                print("added image")

                # Make the experiment
                exp_data = dict(image_id=new_image["id"],
                                pick_type=image["pickstyle"],
                                title=image["challenge"],
                                challenge=image["description"],
                                client_url="dummy")
                exp_url = "{api}/experiments/picking_challenge".format(api=self.new_api)

                exp_data = requests.post(exp_url, json=exp_data,
                                         auth=(new_user_id, dummy_password)).json()
                
                print("added experiment")

                # Interpretations
                interp_url = "{api}/api/picks?image_id={image_id}&all=1".format(
                    image_id=image['image_id'],
                    api=self.old_api)

                interps = requests.get(interp_url).json()
                for interp in interps:

                    int_user_id = self.user_map[interp["user_id"]]
                    data = convert_interps(interp["picks"])

                    interp_post = "{api}/experiment/{exp_id}".format(
                        api=self.new_api, exp_id=exp_data["id"])

                    suc = requests.post(interp_post,
                                        json=data,
                                        auth=(int_user_id, dummy_password))
                    print(suc)
                
            except Exception as e:
                print(e)
    

        
        
    
            
            
    

