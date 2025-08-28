from mongoengine import Document, StringField

class Admin(Document):
    email = StringField(required=True, unique=True)
    password_hash = StringField(required=True)  # Mot de passe haché pour sécurité

    meta = {
        'collection': 'adminsdata',
        'ordering': ['-id']
    }
