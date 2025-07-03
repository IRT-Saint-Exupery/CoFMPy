import os

# Run bash/powershell command to generate FMUs
os.system("pythonfmu build -f scripts_fmus/heat_controller.py --no-external-tool")
os.system("python -m pythonfmu build -f scripts_fmus/heater.py --no-external-tool")
os.system("python -m pythonfmu build -f scripts_fmus/heater_with_loop.py --no-external-tool")
