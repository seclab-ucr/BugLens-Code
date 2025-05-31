import psycopg2
from datetime import datetime
from common.config import DB_CONFIG
import logging

def create_connection():
    return psycopg2.connect(**DB_CONFIG)

__conn = create_connection()

def insert_log(prompt, response, model, round, case_id):
    try:
        cur = __conn.cursor()
        query = """
        INSERT INTO llm_logs (prompt, response, response_at, model, round, case_id) 
        VALUES (%s, %s, %s, %s, %s, %s);
        """
        cur.execute(query, (prompt, response, datetime.now(), model, round, case_id))
        __conn.commit()
        cur.close()
    except (Exception, psycopg2.DatabaseError) as error:
        logging.error(error)

def insert_or_update_varname(case_id, var_name, model):
    try:
        cur = __conn.cursor()
        query = """
        INSERT INTO cases (case_id, var_name, model) 
        VALUES (%s, %s, %s)
        ON CONFLICT (case_id, model) DO UPDATE SET var_name = %s;
        """
        cur.execute(query, (case_id, var_name, model, var_name))
        __conn.commit()
        cur.close()
    except (Exception, psycopg2.DatabaseError) as error:
        logging.error(error)

def insert_or_update_analysis(case_id, analysis_result, model):
    try:
        cur = __conn.cursor()
        query = """
        INSERT INTO cases (case_id, analysis_result, model) 
        VALUES (%s, %s, %s)
        ON CONFLICT (case_id, model) DO UPDATE SET analysis_result = %s;
        """
        cur.execute(query, (case_id, analysis_result, model, analysis_result))
        __conn.commit()
        cur.close()
    except (Exception, psycopg2.DatabaseError) as error:
        logging.error(error)
        
def insert_or_update_sanitizer(case_id, sanitizer_result, model):
    try:
        cur = __conn.cursor()
        query = """
        INSERT INTO cases (case_id, sanitize_result, model) 
        VALUES (%s, %s, %s)
        ON CONFLICT (case_id, model) DO UPDATE SET sanitize_result = %s;
        """
        cur.execute(query, (case_id, sanitizer_result, model, sanitizer_result))
        __conn.commit()
        cur.close()
    except (Exception, psycopg2.DatabaseError) as error:
        logging.error(error)
        
def insert_or_update_req_sanitizer(case_id, req_sanitizer_result, model):
    try:
        cur = __conn.cursor()
        query = """
        INSERT INTO cases (case_id, required_sanitizer, model) 
        VALUES (%s, %s, %s)
        ON CONFLICT (case_id, model) DO UPDATE SET required_sanitizer = %s;
        """
        cur.execute(query, (case_id, req_sanitizer_result, model, req_sanitizer_result))
        __conn.commit()
        cur.close()
    except (Exception, psycopg2.DatabaseError) as error:
        logging.error(error)
        
def get_req_sanitizer(case_id, model):
    try:
        cur = __conn.cursor()
        query = """
        SELECT required_sanitizer FROM cases WHERE case_id = %s AND model = %s;
        """
        cur.execute(query, (case_id, model))
        req_sanitizer = cur.fetchone()
        cur.close()
        return req_sanitizer
    except (Exception, psycopg2.DatabaseError) as error:
        logging.error(error)
        return None
    
    
def insert_or_update_detected_sanitizer(case_id, detected_sanitizer, model):
    try:
        cur = __conn.cursor()
        query = """
        INSERT INTO cases (case_id, detected_sanitizer, model) 
        VALUES (%s, %s, %s)
        ON CONFLICT (case_id, model) DO UPDATE SET detected_sanitizer = %s;
        """
        cur.execute(query, (case_id, detected_sanitizer, model, detected_sanitizer))
        __conn.commit()
        cur.close()
    except (Exception, psycopg2.DatabaseError) as error:
        logging.error(error)


def get_detected_sanitizer(case_id, model):
    try:
        cur = __conn.cursor()
        query = """
        SELECT detected_sanitizer FROM cases WHERE case_id = %s AND model = %s;
        """
        cur.execute(query, (case_id, model))
        sanitizer = cur.fetchone()
        cur.close()
        return sanitizer
    except (Exception, psycopg2.DatabaseError) as error:
        logging.error(error)
        return None

def find_analysis_result(case_id, model):
    try:
        cur = __conn.cursor()
        query = """
        SELECT analysis_result FROM cases WHERE case_id = %s AND model = %s;
        """
        cur.execute(query, (case_id, model))
        analysis_result = cur.fetchone()
        cur.close()
        return analysis_result
    except (Exception, psycopg2.DatabaseError) as error:
        logging.error(error)
        return None
    
def find_case_varname(case_id, model):
    try:
        cur = __conn.cursor()
        query = """
        SELECT var_name FROM cases WHERE case_id = %s AND model = %s;
        """
        cur.execute(query, (case_id, model))
        var_name = cur.fetchone()
        cur.close()
        return var_name
    except (Exception, psycopg2.DatabaseError) as error:
        logging.error(error)
        return None