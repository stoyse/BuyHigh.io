from flask import Blueprint, render_template, g, request, flash, redirect, url_for
from utils import dev_required, login_required
import logging
import database.handler.postgres.postgre_dev_handler as dev_handler
import database.handler.postgres.postgre_education_handler as edu_handler
import database.handler.postgres.postgres_db_handler as db_handler
import database.handler.postgres.postgre_market_mayhem_handler as mayhem_handler
from rich import print
import tools.api_check as api_check
import tools.config as config

logger = logging.getLogger(__name__)

dev_bp = Blueprint('dev', __name__)

@dev_bp.route('/')
@login_required
@dev_required
def index():
    logger.debug("Rendering developer dashboard page")
    
    return render_template(
        'dev/index.html',
        user_count=dev_handler.get_total_user_count(),
        db_size=dev_handler.get_db_size(),
        api_requests=dev_handler.get_api_calls()
    )

@dev_bp.route('/db_explorer')
@login_required
@dev_required
def db_explorer():
    logger.debug("Rendering database explorer page")
    tables = dev_handler.get_all_tables()
    table_data = {}
    for table in tables:
        data = dev_handler.get_table_data(table)
        table_data[table] = data
        logger.debug(f"Data for table {table}: {data}")

    return render_template(
        'dev/db_explorer.html',
        tables=tables,
        table_data=table_data
    )

@dev_bp.route('/daily-quiz', methods=['GET', 'POST'])
def daily_quiz():
    logger.debug("Handling daily quiz submission")
    if request.method == 'POST':
        quizDate = request.form.get('date')
        question = request.form.get('question')
        answer1 = request.form.get('answer1')
        answer2 = request.form.get('answer2')
        answer3 = request.form.get('answer3')
        correct_answer = request.form.get('correct_answer')
        print(f"[purple]Quiz Date: {quizDate}, Question: {question}, Answer1: {answer1}, Answer2: {answer2}, Answer3: {answer3}, Correct Answer: {correct_answer}")
        edu_handler.create_daily_quiz(quizDate, question, answer1, answer2, answer3, correct_answer)
        flash('Quiz submitted successfully!', 'success')
        return redirect(url_for('dev.daily_quiz'))
    
    quizes = edu_handler.get_all_daily_quizzes()
    return render_template('dev/daily_quiz.html', all_quizzes=quizes)

@dev_bp.route('/daily-quiz/delete/<int:quiz_id>', methods=['GET', 'POST'])
@login_required
@dev_required
def delete_daily_quiz(quiz_id):
    logger.debug(f"Deleting daily quiz with ID: {quiz_id}")
    if request.method == 'POST':
        edu_handler.delete_daily_quiz(quiz_id)
        flash('Quiz deleted successfully!', 'success')
        return redirect(url_for('dev.daily_quiz'))
    
    quiz = edu_handler.get_daily_quiz_by_id(quiz_id)
    return render_template('dev/daily_quiz.html', quiz=quiz)

@dev_bp.route('/logs',)
@login_required
@dev_required
def logs():
    logger.debug("Rendering logs page")
    logs = open('logs/app.log', 'r').readlines()
    return render_template('dev/logs.html', logs=logs)

@dev_bp.route('/api-explorer')
@login_required
@dev_required
def api_explorer():
    print(f"[bold green]{api_check.check_api_status()}[/bold green]")
    return render_template('dev/api_explorer.html',
                           api_check=api_check.check_api_status(),
                           api_list=config.API_LIST,
                           base_url=config.BASE_URL)

@dev_bp.route('/user-management')
@login_required
@dev_required
def user_management():
    logger.debug("Rendering user management page")
    print(f"[bold green]{db_handler.get_all_users()}[/bold green]")
    return render_template('dev/user_management.html',
                           all_users=db_handler.get_all_users())

@dev_bp.route('/user-management/delete/<int:user_id>', methods=['GET', 'POST'])
@login_required
@dev_required
def delete_user_view(user_id):  # Name geändert
    logger.debug(f"Deleting user with ID: {user_id}")
    print(f'[red]Deleting user with ID: {user_id}[/]')
    if request.method == 'POST':
        dev_handler.delete_user(user_id)
        flash('User deleted successfully!', 'success')
        return redirect(url_for('dev.user_management'))
    
    return redirect(url_for('dev.user_management'))


@dev_bp.route('/mayhem')
@login_required
@dev_required
def mayhem():
    logger.debug("Rendering mayhem page")
    return render_template('dev/mayhem.html',
                           all_mayhem=mayhem_handler.get_all_mayhem(),
                           check_if_mayhem=mayhem_handler.check_if_mayhem(),
                           mayhem_scenarios=mayhem_handler.get_all_mayhem_scenarios())

@dev_bp.route('/mayhem/shedule/<scenario_id>', methods=['GET', 'POST'])
@login_required
@dev_required
def mayhem_shedule(scenario_id):
    logger.debug(f"Scheduling mayhem for scenario ID: {scenario_id}")
    if request.method == 'POST':
        start_time = request.form.get('start_time')
        end_time = request.form.get('end_time')
        result = request.form.get('result')
        print(f"[purple]Start Time: {start_time}, End Time: {end_time}, Result: {result}")
        
        # Updated function call with all parameters
        mayhem_handler.schedule_mayhem(scenario_id, start_time, end_time, result)
        flash('Mayhem scheduled successfully!', 'success')
        return redirect(url_for('dev.mayhem'))
    
    mayhem_data = mayhem_handler.get_mayhem_data(scenario_id)
    return render_template('dev/mayhem.html', mayhem_data=mayhem_data)