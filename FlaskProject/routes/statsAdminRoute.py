from flask import Blueprint
from controllers.statsAdminController import stats_all,get_unique_students_from_attempts
stats_bp = Blueprint('stats', __name__, url_prefix='/api/stats')

# Une seule route
stats_bp.route('/all', methods=['GET'])(stats_all)


stats_bp.route('/kids', methods=['GET'])(get_unique_students_from_attempts)
