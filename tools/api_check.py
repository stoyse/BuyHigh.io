from flask import Flask, jsonify, request
import tools.config as config

app = Flask(__name__)

def check_api_status():
    """Check the status of all APIs and return a dictionary of results."""
    api_check = config.API_LIST.copy()
    for api_name, api_path in config.API_LIST.items():
        url = f"{config.BASE_URL}{api_path}"
        print(f"Checking {api_name} API at {url}...")
        try:
            # Simulate API check (replace with actual logic if needed)
            response_status = 200  # Mocked status code
            if response_status == 200:
                print(f"{api_name} API is up and running.")
                api_check[api_name]['status'] = True
            else:
                print(f"{api_name} API is down. Status code: {response_status}")
                api_check[api_name]['status'] = False
        except Exception as e:
            print(f"Error checking {api_name} API: {e}")
            api_check[api_name]['status'] = False
    return api_check

@app.route('/check_api_status', methods=['GET'])
def api_status_endpoint():
    """Flask route that returns the API status as JSON."""
    return jsonify(check_api_status())

if __name__ == '__main__':
    app.run(debug=True)