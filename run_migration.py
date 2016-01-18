from migrate import PTMigrate

old_url = 'http://dev.pick-this.appspot.com/'
new_url = 'http://localhost:5000'
user_map = 'user_map.json'

mig = PTMigrate(old_url, new_url)
mig.migrate_users(mapfile=user_map)

#mig = PTMigrate(old_url, new_url, user_file=user_map)

mig.migrate_images()



