# data_layer.py (слой данных)
import os
import uuid
import pandas as pd
from sqlalchemy import create_engine

class DataManager:
    def __init__(self):
        self.sessions = {}
        self.engine = create_engine('sqlite:///data.db')

    def load_data(self, file):
        if file.filename.endswith('.csv'):
            df = pd.read_csv(file)
        else:
            df = pd.read_excel(file)
        return df

    def save_to_session(self, df, analysis_type):
        session_id = str(uuid.uuid4())
        self.sessions[session_id] = {
            'data': df,
            'type': analysis_type
        }
        return session_id

    def get_session_data(self, session_id):
        return self.sessions[session_id]['data']

    def update_session(self, session_id, new_df):
        self.sessions[session_id]['data'] = new_df