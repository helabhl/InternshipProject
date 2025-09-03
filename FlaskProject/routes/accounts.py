from flask import Blueprint, request, jsonify
from models.account import AccountData
from werkzeug.security import generate_password_hash
accounts_bp = Blueprint("accountsdata", __name__)


@accounts_bp.route('/accounts', methods=['POST'])
def create_account():
    data = request.get_json()
    try:
        # Si tu as un champ "password" dans data, on le hash
        # if "password_hash" in data:
        #     data["password_hash"] = generate_password_hash(data["password_hash"])
        
        account = AccountData(**data)
        account.save()
        return jsonify({"message": "Account created", "id": str(account.id)}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 400
    
@accounts_bp.route('/accounts', methods=['GET'])
def get_all_accounts():
    accounts = AccountData.objects()  # récupère tous les comptes
    accounts_list = []

    for account in accounts:
        acc_dict = account.to_mongo().to_dict()
        acc_dict["_id"] = str(acc_dict["_id"])  # convertir ObjectId en string
        accounts_list.append(acc_dict)

    return jsonify(accounts_list), 200



@accounts_bp.route('/accounts/<user_id>', methods=['GET'])
def get_account(user_id):
    account = AccountData.objects(userID=user_id).first()
    if not account:
        return jsonify({"error": "Account not found"}), 404

    account_dict = account.to_mongo().to_dict()
    account_dict["_id"] = str(account_dict["_id"])
    return jsonify(account_dict), 200




@accounts_bp.route('/accounts/<user_id>/kids', methods=['GET'])
def get_kids(user_id):
    # Chercher le compte du parent
    account = AccountData.objects(userID=user_id).first()
    if not account:
        return jsonify({"error": "Account not found"}), 404

    # Récupérer les enfants
    kids_dict = account.kids  # MapField -> dict
    # Convertir les EmbeddedDocuments en dicts
    kids_serialized = {k: v.to_mongo().to_dict() for k, v in kids_dict.items()}

    return jsonify({
        "userID": account.userID,
        "kids": kids_serialized
    }), 200

@accounts_bp.route("/get_kids_names/<user_id>")
def get_kids_names(user_id):
    # Chercher le compte du parent
    account = AccountData.objects(userID=user_id).first()
    if not account:
        return jsonify({"error": "Account not found"}), 404

    # Récupérer les enfants
    kids_dict = account.kids  # MapField -> dict
    # Convertir les EmbeddedDocuments en dicts
    kids_serialized = {k: v.to_mongo().to_dict() for k, v in kids_dict.items()}

    # Transformer l'objet kids en liste de noms
    kids_names = {key:kid["name"] for key, kid in kids_serialized.items()}
    
    return jsonify( kids_names)

