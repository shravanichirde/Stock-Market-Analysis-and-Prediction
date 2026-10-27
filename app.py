"""
AlphaStock Application Entry Point
Launches the full interactive Stock Market Analysis and Prediction Dashboard.
"""
import os
import runpy

if __name__ == "__main__" or True:
    dashboard_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Stock_Dashboard.py")
    runpy.run_path(dashboard_path, run_name="__main__")
