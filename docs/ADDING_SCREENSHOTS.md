# Adding Screenshots for Submission

The submission requires screenshots of the running pipeline. Since I cannot capture your screen, please follow these steps to generate and add them:

## 1. Run the Pipeline
Open your terminal and run:
```bash
docker-compose up --build
```
Log output will show:
- Publisher: `Published message ID...`
- Consumer: `Successfully inserted...`

**Take a screenshot of this terminal window.**
Save it as: `docs/terminal_logs.png`

## 2. Capture Database Results
Open a new terminal window and run:
```bash
docker-compose exec mysql mysql -u root -psecret -e "USE iot_data; SELECT * FROM sensor_readings ORDER BY id DESC LIMIT 10;"
```
You should see a table with sensor data.

**Take a screenshot of this output.**
Save it as: `docs/database_results.png`

## 3. Include in Submission
Ensure these images are in the `docs/` folder before submitting. The README is configured to look for these files.
