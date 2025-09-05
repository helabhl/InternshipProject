from models.account import AccountData
from bson import ObjectId


def mongo_to_dict(obj):
    """Convertir un document MongoEngine en dict avec _id en string"""
    data = obj.to_mongo().to_dict()
    data["_id"] = str(data["_id"])
    return data


def create_account(data):
    try:
        account = AccountData(**data)
        account.save()
        return {"message": "Account created", "id": str(account.id)}, 201
    except Exception as e:
        return {"error": str(e)}, 400


def get_all_accounts():
    accounts = AccountData.objects()
    accounts_list = [mongo_to_dict(acc) for acc in accounts]
    return accounts_list, 200


def get_account(user_id):
    account = AccountData.objects(userID=user_id).first()
    if not account:
        return {"error": "Account not found"}, 404
    return mongo_to_dict(account), 200


def get_kids(user_id):
    account = AccountData.objects(userID=user_id).first()
    if not account:
        return {"error": "Account not found"}, 404

    kids_dict = account.kids  # MapField -> dict
    kids_serialized = {k: v.to_mongo().to_dict() for k, v in kids_dict.items()}

    return {
        "userID": account.userID,
        "kids": kids_serialized
    }, 200


def get_kids_names(user_id):
    account = AccountData.objects(userID=user_id).first()
    if not account:
        return {"error": "Account not found"}, 404

    kids_dict = account.kids
    kids_serialized = {k: v.to_mongo().to_dict() for k, v in kids_dict.items()}
    kids_names = {key: kid["name"] for key, kid in kids_serialized.items()}

    return kids_names, 200


