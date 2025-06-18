from flask import Flask, render_template, request, jsonify, send_from_directory, redirect, url_for, request, session, flash
import pandas as pd
import numpy as np
import pickle
import joblib
import json
import os
import logging
from datetime import datetime
from functools import wraps
app = Flask(__name__)
app.secret_key = 'your_secret_key_here'  # Replace with a secure random key

# In-memory store for demo: {customer_id: password}
customer_users = {}

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session or 'role' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def employee_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get('role') != 'employee':
            flash('Access denied: Employees only.', 'danger')
            return redirect(url_for('home'))
        return f(*args, **kwargs)
    return decorated_function


# Configure logging
logging.basicConfig(level=logging.DEBUG)

# File to store application data
DATA_FILE = 'data/applications.json'

def load_applications_from_file():
    """Load applications from JSON file with improved error handling"""
    try:
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, 'r') as f:
                data = json.load(f)
                if isinstance(data, list) and len(data) > 0:
                    print(f"Loaded {len(data)} applications from file")
                    return data
                else:
                    print("File exists but contains invalid data")
        else:
            print("Data file does not exist")
    except Exception as e:
        print(f"Error loading applications from file: {e}")
    
    print("Generating initial data...")
    return generate_initial_data()

def save_applications_to_file(applications):
    """Save applications to JSON file with improved error handling"""
    try:
        os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
        with open(DATA_FILE, 'w') as f:
            json.dump(applications, f, indent=2)
        print(f"Saved {len(applications)} applications to file")
        return True
    except Exception as e:
        print(f"Error saving applications to file: {e}")
        return False

def generate_initial_data():
    """Generate initial sample data"""
    names = ['John Smith', 'Sarah Johnson', 'Mike Davis', 'Emily Wilson', 'David Brown', 
             'Lisa Garcia', 'Tom Wilson', 'Anna Martinez', 'Chris Lee', 'Maria Rodriguez',
             'James Taylor', 'Jennifer White', 'Robert Anderson', 'Jessica Thomas', 'Michael Jackson',
             'Ashley Brown', 'Kevin Miller', 'Amanda Davis', 'Daniel Wilson', 'Michelle Garcia']
    
    applications = []
    
    for i in range(1, 31):
        risk_score = np.random.random()
        # Ensure we have a good mix of statuses
        if i <= 12:
            status = 'Pending'
        elif i <= 20:
            status = 'Approved'
        elif i <= 25:
            status = 'Rejected'
        else:
            status = 'Under Review'
            
        applications.append({
            'id': f"LN{datetime.now().year}{str(i).zfill(3)}",
            'applicant': np.random.choice(names),
            'amount': int(np.random.randint(5000, 50000)),
            'riskScore': round(risk_score, 3),
            'status': status,
            'date': (datetime.now() - pd.Timedelta(days=np.random.randint(0, 30))).strftime('%Y-%m-%d'),
            'creditScore': int(np.random.randint(550, 850)),
            'income': int(np.random.randint(30000, 120000)),
            'dti': round(np.random.random() * 0.5, 3),
            'created_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'updated_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })
    
    print(f"Generated {len(applications)} initial applications")
    save_applications_to_file(applications)
    return applications

# Initialize applications data
print("Initializing applications data...")
applications_data = load_applications_from_file()
print(f"Applications data initialized with {len(applications_data) if applications_data else 0} records")

# Load the trained model (if available)
try:
    model_path = 'models/loan_model.pkl'
    if os.path.exists(model_path):
        model_package = joblib.load(model_path)
        model = model_package.get('best_model') or model_package.get('model')
        scaler = model_package.get('scaler')
        label_encoders = model_package.get('label_encoders', {})
        feature_columns = model_package.get('feature_columns', [])
        model_name = model_package.get('model_name', 'Unknown')
        print(f"✅ Model loaded successfully: {model_name}")
    else:
        model = None
        scaler = None
        label_encoders = {}
        feature_columns = []
        model_name = "Demo Mode"
        print("⚠️ Model file not found - using demo predictions")
except Exception as e:
    model = None
    scaler = None
    label_encoders = {}
    feature_columns = []
    model_name = "Demo Mode"
    print(f"⚠️ Error loading model: {e} - using demo predictions")

# Sample insights data
INSIGHTS_DATA = {
    'total_loans': 50000,
    'avg_loan_amount': 15000,
    'approval_rate': 0.78,
    'avg_interest_rate': 0.12,
    'top_risk_factors': ['Credit Score', 'Income Level', 'DTI Ratio', 'Employment History', 'Loan Amount'],
    'grade_distribution': {'A': 0.25, 'B': 0.30, 'C': 0.25, 'D': 0.15, 'E': 0.05},
    'model_accuracy': 0.89,
    'best_model': 'Random Forest',
    'avg_prediction_error': 2150
}

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        login_type = request.form.get('login_type')
        user_id = request.form.get('user_id')
        password = request.form.get('password')

        if login_type == 'employee':
            if user_id == 'admin' and password == 'admin':
                session['user_id'] = user_id
                session['role'] = 'employee'
                flash('Employee login successful.', 'success')
                return redirect(url_for('dashboard'))
            else:
                flash('Invalid employee credentials.', 'danger')
        elif login_type == 'customer':
            if user_id and password:
                # Save customer credentials (in-memory for demo)
                customer_users[user_id] = password
                session['user_id'] = user_id
                session['role'] = 'customer'
                flash('Customer login successful.', 'success')
                return redirect(url_for('index'))
            else:
                flash('Please enter both ID and password.', 'danger')
        else:
            flash('Please select a login type.', 'danger')

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out successfully.', 'info')
    return redirect(url_for('login'))


# Add request/response logging
@app.before_request
def log_request_info():
    app.logger.debug('Request: %s %s', request.method, request.url)

@app.after_request
def log_response_info(response):
    app.logger.debug('Response: %s', response.status)
    return response

@app.route('/')
def index():
    """Home page with platform overview"""
    return render_template('index.html', insights=INSIGHTS_DATA)

@app.route('/insights')
@login_required
def insights():
    """Insights page displaying ML analysis results"""
    return render_template('insights.html', insights=INSIGHTS_DATA)

@app.route('/calculator')
@login_required
def calculator():
    """Loan calculator page"""
    return render_template('calculator.html')

@app.route('/eligibility')
@login_required
def eligibility():
    """Loan eligibility checker page"""
    return render_template('eligibility.html')

@app.route('/dashboard')
@login_required
@employee_required
def dashboard():
    """Employee dashboard for loan decision support"""
    return render_template('dashboard.html')

@app.route('/test')
def test():
    """Test route to check if Flask is working"""
    return jsonify({
        "status": "working", 
        "applications_count": len(applications_data) if applications_data else 0,
        "timestamp": datetime.now().isoformat()
    })

# API Routes for Applications
@app.route('/api/applications', methods=['GET'])
def get_applications():
    """Get all applications with improved error handling and sorting"""
    try:
        global applications_data
        
        print(f"API call to /api/applications - Current data length: {len(applications_data) if applications_data else 0}")
        
        # Ensure applications_data exists and is not None
        if applications_data is None or len(applications_data) == 0:
            print("No applications data found, generating initial data...")
            applications_data = generate_initial_data()
        
        # Ensure it's a list
        if not isinstance(applications_data, list):
            print("Applications data is not a list, regenerating...")
            applications_data = generate_initial_data()
        
        # Sort applications by date (newest first)
        sorted_applications = sorted(
            applications_data,
            key=lambda x: x.get('date', '1970-01-01'),
            reverse=True
        )
        
        print(f"Returning {len(sorted_applications)} applications")
        return jsonify(sorted_applications)
        
    except Exception as e:
        print(f"Error in get_applications: {e}")
        app.logger.error(f"Error in get_applications: {e}")
        return jsonify({'error': 'Failed to load applications'}), 500

@app.route('/api/applications', methods=['POST'])
def create_application():
    """Create new application with enhanced validation"""
    try:
        global applications_data
        data = request.json
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Validate required fields
        required_fields = ['applicant', 'income', 'creditScore', 'amount', 'dti']
        for field in required_fields:
            if field not in data or not str(data[field]).strip():
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # Convert and validate numeric fields
        try:
            income = int(data['income'])
            credit_score = int(data['creditScore'])
            amount = int(data['amount'])
            dti = float(data['dti'])
            
            if income <= 0 or amount <= 0:
                return jsonify({'error': 'Income and amount must be positive'}), 400
            if not (300 <= credit_score <= 850):
                return jsonify({'error': 'Credit score must be between 300 and 850'}), 400
            if not (0 <= dti <= 1):
                return jsonify({'error': 'DTI ratio must be between 0 and 1'}), 400
        except ValueError as e:
            return jsonify({'error': f'Invalid numeric value: {str(e)}'}), 400
        
        # Generate ID with current year
        current_year = datetime.now().year
        next_id = len(applications_data) + 1
        app_id = f"LN{current_year}{str(next_id).zfill(4)}"
        
        new_app = {
            'id': app_id,
            'applicant': data['applicant'].strip(),
            'amount': amount,
            'status': 'Pending',
            'riskScore': calculate_risk_score(data),
            'date': datetime.now().strftime('%Y-%m-%d'),
            'creditScore': credit_score,
            'income': income,
            'dti': dti,
            'created_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'updated_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        applications_data.append(new_app)
        save_applications_to_file(applications_data)
        
        return jsonify({'success': True, 'application': new_app})
        
    except Exception as e:
        print(f"Error creating application: {e}")
        app.logger.error(f"Error creating application: {e}")
        return jsonify({'error': 'Failed to create application'}), 500

@app.route('/api/applications/<app_id>/status', methods=['PUT'])
def update_application_status(app_id):
    """Update application status with enhanced validation"""
    try:
        global applications_data
        data = request.json
        
        if not data or 'status' not in data:
            return jsonify({'error': 'Status not provided'}), 400
        
        valid_statuses = ['Pending', 'Approved', 'Rejected', 'Under Review']
        if data['status'] not in valid_statuses:
            return jsonify({'error': f'Invalid status. Must be one of: {", ".join(valid_statuses)}'}), 400
        
        app_found = False
        for app in applications_data:
            if app['id'] == app_id:
                app['status'] = data['status']
                app['updated_date'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                app_found = True
                break
        
        if not app_found:
            return jsonify({'error': 'Application not found'}), 404
        
        save_applications_to_file(applications_data)
        return jsonify({'success': True, 'message': f'Status updated to {data["status"]}'})
        
    except Exception as e:
        print(f"Error updating application status: {e}")
        app.logger.error(f"Error updating application status: {e}")
        return jsonify({'error': 'Failed to update status'}), 500

@app.route('/api/dashboard_stats')
def get_dashboard_stats():
    """Get dashboard statistics with improved error handling"""
    try:
        global applications_data
        
        print(f"API call to /api/dashboard_stats - Current data length: {len(applications_data) if applications_data else 0}")
        
        # Ensure we have data
        if not applications_data or len(applications_data) == 0:
            print("No data for stats, generating initial data...")
            applications_data = generate_initial_data()
            
        pending = len([app for app in applications_data if app.get('status') == 'Pending'])
        approved = len([app for app in applications_data if app.get('status') == 'Approved'])
        rejected = len([app for app in applications_data if app.get('status') == 'Rejected'])
        total = len(applications_data)
        
        approval_rate = (approved / total * 100) if total > 0 else 0
        total_disbursed = sum(app.get('amount', 0) for app in applications_data if app.get('status') == 'Approved')
        
        stats = {
            'pending': pending,
            'approved': approved,
            'rejected': rejected,
            'approval_rate': round(approval_rate, 1),
            'total_disbursed': total_disbursed
        }
        
        print(f"Dashboard stats: {stats}")
        return jsonify(stats)
        
    except Exception as e:
        print(f"Error in get_dashboard_stats: {e}")
        app.logger.error(f"Error in get_dashboard_stats: {e}")
        return jsonify({
            'pending': 0,
            'approved': 0,
            'rejected': 0,
            'approval_rate': 0,
            'total_disbursed': 0
        })

def calculate_risk_score(data):
    """Calculate risk score for new application"""
    try:
        score = 0
        
        # Credit score impact (40%)
        credit_score = int(data.get('creditScore', 600))
        if credit_score >= 750:
            score += 0.4
        elif credit_score >= 700:
            score += 0.35
        elif credit_score >= 650:
            score += 0.25
        elif credit_score >= 600:
            score += 0.15
        else:
            score += 0.05
        
        # DTI ratio impact (25%)
        dti = float(data.get('dti', 0.5))
        if dti <= 0.2:
            score += 0.25
        elif dti <= 0.3:
            score += 0.20
        elif dti <= 0.4:
            score += 0.10
        else:
            score += 0.0
        
        # Income impact (20%)
        income = int(data.get('income', 30000))
        if income >= 75000:
            score += 0.20
        elif income >= 50000:
            score += 0.15
        elif income >= 30000:
            score += 0.10
        else:
            score += 0.05
        
        # Loan-to-income ratio (15%)
        amount = int(data.get('amount', 10000))
        loan_to_income = amount / income if income > 0 else 1
        if loan_to_income <= 0.3:
            score += 0.15
        elif loan_to_income <= 0.5:
            score += 0.10
        else:
            score += 0.0
        
        return min(score, 0.99)
    except Exception as e:
        print(f"Error calculating risk score: {e}")
        return 0.5  # Default risk score

@app.route('/predict_eligibility', methods=['POST'])
def predict_eligibility():
    """API endpoint for loan eligibility prediction"""
    try:
        data = request.json
        
        features = {
            'income': float(data.get('income', 0)),
            'credit_score': float(data.get('credit_score', 0)),
            'loan_amount': float(data.get('loan_amount', 0)),
            'dti_ratio': float(data.get('dti_ratio', 0)),
            'employment_length': int(data.get('employment_length', 0))
        }
        
        # Validate input ranges
        if not (300 <= features['credit_score'] <= 850):
            return jsonify({'error': 'Credit score must be between 300 and 850'}), 400
        
        if not (0 <= features['dti_ratio'] <= 1):
            return jsonify({'error': 'DTI ratio must be between 0 and 1'}), 400
        
        if features['income'] <= 0 or features['loan_amount'] <= 0:
            return jsonify({'error': 'Income and loan amount must be positive'}), 400
        
        # Use rule-based prediction
        approval_probability = calculate_rule_based_probability(features)
        
        # Calculate loan terms
        terms_data = calculate_loan_terms(features, approval_probability)
        
        return jsonify(terms_data)
        
    except ValueError as e:
        return jsonify({'error': f'Invalid input data: {str(e)}'}), 400
    except Exception as e:
        return jsonify({'error': f'Prediction error: {str(e)}'}), 500

def calculate_rule_based_probability(features):
    """Calculate approval probability using rule-based system"""
    score = 0
    
    # Credit score impact (40% weight)
    if features['credit_score'] >= 750:
        score += 40
    elif features['credit_score'] >= 700:
        score += 35
    elif features['credit_score'] >= 650:
        score += 25
    elif features['credit_score'] >= 600:
        score += 15
    else:
        score += 5
    
    # DTI ratio impact (25% weight)
    if features['dti_ratio'] <= 0.2:
        score += 25
    elif features['dti_ratio'] <= 0.3:
        score += 20
    elif features['dti_ratio'] <= 0.4:
        score += 10
    else:
        score += 0
    
    # Income impact (20% weight)
    if features['income'] >= 75000:
        score += 20
    elif features['income'] >= 50000:
        score += 15
    elif features['income'] >= 30000:
        score += 10
    else:
        score += 5
    
    # Employment length impact (10% weight)
    if features['employment_length'] >= 3:
        score += 10
    elif features['employment_length'] >= 2:
        score += 7
    elif features['employment_length'] >= 1:
        score += 5
    else:
        score += 2
    
    # Loan-to-income ratio impact (5% weight)
    loan_to_income = features['loan_amount'] / features['income']
    if loan_to_income <= 0.3:
        score += 5
    elif loan_to_income <= 0.5:
        score += 3
    else:
        score += 0
    
    # Convert to probability (0-1)
    probability = min(score / 100, 0.95)  # Cap at 95%
    return probability

def calculate_loan_terms(features, approval_probability):
    """Calculate loan terms based on approval probability and features"""
    
    # Determine status
    if approval_probability >= 0.7:
        status = "Approved"
        base_rate = 0.06
    elif approval_probability >= 0.5:
        status = "Likely Approved"
        base_rate = 0.09
    elif approval_probability >= 0.3:
        status = "Conditional Approval"
        base_rate = 0.12
    else:
        status = "Needs Improvement"
        base_rate = 0.15
    
    # Adjust interest rate based on risk factors
    interest_rate = base_rate
    
    # Credit score adjustment
    if features['credit_score'] < 650:
        interest_rate += 0.03
    elif features['credit_score'] >= 750:
        interest_rate -= 0.01
    
    # DTI ratio adjustment
    if features['dti_ratio'] > 0.4:
        interest_rate += 0.02
    elif features['dti_ratio'] <= 0.2:
        interest_rate -= 0.005
    
    # Employment length adjustment
    if features['employment_length'] < 2:
        interest_rate += 0.01
    
    # Cap interest rate
    interest_rate = min(max(interest_rate, 0.05), 0.25)
    
    # Calculate monthly payment (assuming 36-month term)
    term_months = 36
    monthly_rate = interest_rate / 12
    if monthly_rate == 0:
        monthly_payment = features['loan_amount'] / term_months
    else:
        monthly_payment = features['loan_amount'] * (monthly_rate * (1 + monthly_rate)**term_months) / ((1 + monthly_rate)**term_months - 1)
    
    # Generate terms description
    if approval_probability >= 0.7:
        terms = "Excellent terms with competitive rates and flexible repayment options"
    elif approval_probability >= 0.5:
        terms = "Standard terms with moderate conditions"
    elif approval_probability >= 0.3:
        terms = "Conditional approval - may require additional documentation or co-signer"
    else:
        terms = "Consider improving credit score, reducing DTI ratio, or applying for a smaller amount"
    
    return {
        'approval_probability': round(approval_probability * 100, 1),
        'status': status,
        'interest_rate': round(interest_rate * 100, 2),
        'terms': terms,
        'monthly_payment': round(monthly_payment, 2),
        'total_payment': round(monthly_payment * term_months, 2),
        'total_interest': round((monthly_payment * term_months) - features['loan_amount'], 2)
    }

@app.route('/calculate_loan', methods=['POST'])
def calculate_loan():
    """API endpoint for loan payment calculation"""
    try:
        data = request.json
        
        print(f"Received loan calculation data: {data}")
        
        principal = float(data.get('principal', 0))
        rate = float(data.get('rate', 0))
        term = int(data.get('term', 0))
        
        print(f"Principal: {principal}, Rate: {rate}%, Term: {term} months")
        
        # Validation
        if principal <= 0:
            return jsonify({'error': 'Loan amount must be positive'}), 400
        if rate < 0:
            return jsonify({'error': 'Interest rate cannot be negative'}), 400
        if term <= 0:
            return jsonify({'error': 'Loan term must be positive'}), 400
        
        # Convert annual percentage rate to monthly decimal rate
        monthly_rate = (rate / 100) / 12
        
        print(f"Monthly rate: {monthly_rate}")
        
        # Calculate monthly payment using the standard loan formula
        if monthly_rate == 0:
            monthly_payment = principal / term
        else:
            monthly_payment = principal * (monthly_rate * (1 + monthly_rate)**term) / ((1 + monthly_rate)**term - 1)
        
        # Calculate totals
        total_payment = monthly_payment * term
        total_interest = total_payment - principal
        
        print(f"Monthly payment: {monthly_payment}")
        
        result = {
            'monthly_payment': round(monthly_payment, 2),
            'total_payment': round(total_payment, 2),
            'total_interest': round(total_interest, 2),
            'principal': round(principal, 2),
            'effective_annual_rate': round(rate, 2)
        }
        
        print(f"Returning result: {result}")
        return jsonify(result)
        
    except ValueError as e:
        print(f"ValueError: {e}")
        return jsonify({'error': f'Invalid input: {str(e)}'}), 400
    except Exception as e:
        print(f"Exception: {e}")
        return jsonify({'error': f'Calculation error: {str(e)}'}), 500

@app.route('/favicon.ico')
def favicon():
    try:
        return send_from_directory(os.path.join(app.root_path, 'static'), 
                                 'favicon.ico', mimetype='image/vnd.microsoft.icon')
    except:
        return '', 204

@app.errorhandler(404)
def not_found_error(error):
    try:
        return render_template('404.html'), 404
    except:
        return '<h1>404 - Page Not Found</h1><p>The page you are looking for does not exist.</p>', 404

@app.errorhandler(500)
def internal_error(error):
    try:
        return render_template('500.html'), 500
    except:
        return '<h1>500 - Internal Server Error</h1><p>Something went wrong on our end.</p>', 500

@app.route('/health')
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'model_loaded': model is not None,
        'model_name': model_name,
        'total_applications': len(applications_data) if applications_data else 0
    })

if __name__ == '__main__':
    # Create necessary directories
    os.makedirs('models', exist_ok=True)
    os.makedirs('static/images', exist_ok=True)
    os.makedirs('data', exist_ok=True)
    
    print("🚀 Starting Loan Insights Platform...")
    print(f"📊 Model Status: {model_name}")
    print(f"📋 Applications Loaded: {len(applications_data) if applications_data else 0}")
    print(f"🔗 Access the application at: http://localhost:5000")
    
    app.run(debug=True, host='0.0.0.0', port=5000)