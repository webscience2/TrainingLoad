

# **A Scientific and Technical Framework for a Personalized Multi-Sport Training Protocol**

## **Part I: The Scientific Foundation of a Dynamic Training Protocol**

### **Section 1: The Physiology of Adaptation and Progressive Overload**

#### **1.1 The Principle of Progressive Overload**

The cornerstone of all physiological improvement in athletics is the principle of progressive overload. This principle dictates that for the human body to adapt—whether by increasing muscle size, strength, or endurance—it must be subjected to a training stress that is greater than what it is accustomed to. The body will not change unless it is forced to adapt to a new stimulus. This concept is foundational to both resistance training and cardiovascular exercise, making it directly applicable to a combined running and cycling program.

The mechanism of action involves a systematic and gradual increase in training difficulty, pushing the athlete out of their comfort zone. For endurance athletes, this "overload" component refers to performing workouts at a volume and intensity that exceed the current capacity of the muscles and metabolic systems, within reasonable limits. This stress induces microscopic tears and structural damage in muscle fibers. While this sounds counterintuitive, it is this controlled damage that stimulates the body's repair and rebuilding processes. Following a period of adequate recovery, this leads to supercompensation, where the tissues are rebuilt stronger and more resilient than before, ultimately resulting in gains in muscular strength, size (hypertrophy), and endurance.

In a combined running and cycling program, progressive overload is achieved by manipulating three key variables over time:

* **Intensity:** This refers to how hard a workout is. It can be increased by adding more weight or resistance, running or cycling at a faster pace, or tackling steeper inclines.  
* **Volume/Duration:** This refers to the total amount of work performed. It can be increased by adding more repetitions or sets in a strength workout, or by extending the duration or distance of a run or ride.  
* **Frequency:** This refers to how often an athlete trains. Increasing the number of running or cycling sessions per week is a direct way to increase the total training stimulus.

It is critical that this progression is gradual. Increasing the training stimulus too quickly elevates the risk of injury, while progressing too slowly can lead to a fitness plateau where adaptations cease.

#### **1.2 The Dose-Response Relationship and Maladaptation**

The relationship between training and performance can be conceptualized as a dose-response model, where the daily training load is the "dose" and the resulting change in performance is the "response". The goal of any training program is to administer a dose sufficient to stimulate a positive adaptation. However, this process exists on a delicate spectrum, and the line between beneficial stress and harmful overwork is thin. The physiological response to training can be categorized into a continuum of fatigue states:

* **Acute Fatigue (AF):** The normal, short-term tiredness and performance decline that follows a training session or a few days of hard training. This is a necessary component of the training process.  
* **Functional Overreaching (FOR):** A state achieved through a purposeful, short-term block of intensified training. It results in a temporary performance decrement, but after a period of recovery (days to a couple of weeks), it is followed by a supercompensation effect, leading to an improved performance output.  
* **Non-Functional Overreaching (NFOR):** This occurs when the training load is excessively high without adequate recovery. The performance decrement is more severe and prolonged, and it can take several weeks or even months to fully recover. NFOR is often accompanied by psychological and hormonal disturbances and represents a state of maladaptation.  
* **Overtraining Syndrome (OTS):** The most severe state of maladaptation, characterized by a long-term performance decrement lasting several months or more. OTS involves significant physiological, immunological, and psychological disturbances, including sleep issues, illness, and mood changes. It represents a systemic failure to cope with training stress.

The fundamental challenge for any training protocol, whether designed by a human coach or an algorithm, is to navigate this spectrum effectively. The system must apply a sufficient overload to induce FOR while rigorously avoiding the transition into NFOR and OTS. This requires a sophisticated method of quantifying the training dose and monitoring the athlete's response to it, ensuring that periods of overload are always balanced with adequate recovery.

A common heuristic for managing load progression is the "10% rule," which suggests not increasing weekly volume by more than 10%. However, this is a blunt instrument that fails to account for the intensity of the training or the athlete's individual state of fitness and fatigue. A truly personalized system must move beyond such fixed percentages. The danger of an overly aggressive load increase is not merely a lack of progress, but a heightened risk of overuse injuries. An athlete's aerobic system adapts to training within days, leading to a subjective feeling of rapidly improving fitness. This can create a dangerous disconnect, as the connective tissues—muscles, tendons, and bones—take weeks or even months to adapt and strengthen in response to higher loads. An algorithm's primary role is to bridge this gap, using objective data to govern the training load and prevent the athlete from increasing their workload faster than their structural tissues can handle, thereby mitigating the risk of common overuse injuries like runner's knee, shin splints, and stress fractures.

### **Section 2: A Unified Framework for Quantifying Multi-Sport Training Stress**

#### **2.1 The Need for a Universal Load Metric**

For an athlete engaged in both running and cycling, quantifying the total training stress presents a significant challenge. Simply adding up the duration or distance of workouts is misleading; a 5 km high-intensity interval run imposes a vastly different physiological stress than a 5 km easy recovery run. Furthermore, comparing the stress of a 90-minute run to a 90-minute bike ride is not straightforward due to differences in muscle recruitment, weight-bearing impact, and cardiovascular demands. To effectively manage the total dose of training and recovery, a unified scoring system is required—a common "currency" of physiological stress that can be applied across different activities. This allows for the summation of daily and weekly training loads into a single, meaningful number.

#### **2.2 Internal Load Quantification: Training Impulse (TRIMP)**

Training Impulse (TRIMP) is a well-established method for quantifying training load based on internal physiological markers, specifically heart rate. It combines the duration of a workout with its intensity, derived from heart rate data, to produce a single load score.

There are several methods for calculating TRIMP, with the most prominent being:

* Banister's TRIMP (TRIMPexp): This is the original method, which uses an exponential weighting factor to account for the non-linear increase in physiological stress (as measured by blood lactate) at higher heart rates. The formula is:

  TRIMP=Time (min)×ΔHR×0.64e(k×ΔHR)

  Where ΔHR is the Heart Rate Reserve fraction (Avg HR \- Rest HR) / (Max HR \- Rest HR), and k is a gender-specific coefficient (1.92 for men, 1.67 for women).  
* **Zonal TRIMP (Edwards' TRIMP):** This is a simpler, linearized method that assigns a multiplier to the time spent in each of five predefined heart rate zones. For example, one minute in Zone 1 might be worth 1 point, a minute in Zone 2 worth 2 points, and so on. The total TRIMP is the sum of the points accumulated across all zones.

The primary advantage of TRIMP is its objectivity and its applicability across any endurance sport where heart rate is a valid indicator of effort. However, its reliance on heart rate is also its main weakness. Heart rate can be influenced by factors other than exercise intensity, such as heat, dehydration, caffeine, and psychological stress, potentially skewing the load score.1 Furthermore, heart rate is slow to respond to rapid changes in effort, making it less accurate for quantifying the stress of short, high-intensity intervals. It also tends to underestimate the load of anaerobic or neuromuscularly demanding activities like sprinting or strength training.

#### **2.3 External Load Quantification: Training Stress Score (TSS)**

Training Stress Score (TSS) is a concept, modeled after TRIMP, that quantifies training load based on external work performed relative to an athlete's functional threshold. The functional threshold represents the highest intensity an athlete can sustain for approximately one hour. By definition, one hour of exercise performed exactly at this threshold intensity equates to a score of 100 TSS.

* Cycling TSS (power-based): This is considered the most accurate method for quantifying training load. It is calculated using power meter data, which is a direct measure of the work being performed. The formula incorporates Normalized Power (NP), a metric that accounts for the physiological cost of variable intensity efforts better than average power.

  TSS=(FTP×3600)(Seconds×NP×IF)​×100

  Where NP is Normalized Power, FTP is Functional Threshold Power, and IF (Intensity Factor) is the ratio of NP to FTP.  
* Running TSS (rTSS, pace-based): For running, where power meters are less common, a similar score is calculated using pace as the measure of intensity. The calculation uses Normalized Graded Pace (NGP), which adjusts for the increased physiological cost of running uphill and the decreased cost of running downhill, to provide a more accurate representation of effort on varied terrain.

  rTSS=(FThP×3600)(Seconds×NGP×IF)​×100

  Where NGP is Normalized Graded Pace, FThP is Functional Threshold Pace, and IF is the ratio of NGP to FThP.

#### **2.4 A Proposed Hybrid Model for Unified Load Scoring**

To create a robust and accurate system for a multi-sport athlete, the algorithm must leverage the best available data for each activity. Therefore, a hierarchical approach to calculating a daily **Unified Training Load (UTL)** is proposed.

1. **For Cycling Activities:** The system will prioritize power-based TSS. If a power meter was used and valid power data is present in the activity file, this method will be used.  
2. **For Running Activities:** The system will use pace-based rTSS, provided there is valid GPS or footpod data to calculate NGP.  
3. **Fallback Method:** For any activity lacking the primary data source (e.g., a cycling session on a trainer without a power meter, an indoor run on a treadmill without a footpod, or any other sport), the system will default to calculating a heart rate-based score, such as Heart Rate TSS (hrTSS) or Banister's TRIMP.

The total UTL for any given day will be the simple summation of the scores from all completed activities. This approach is consistent with major platforms like Garmin and COROS, which use a single, modality-agnostic load metric (based on EPOC or TRIMP, respectively) to quantify an athlete's total stress. This pragmatic solution treats a 100 UTL run and a 100 UTL bike ride as equivalent in terms of their systemic physiological stress, allowing for the management of a single, comprehensive training load.

The integrity of this entire framework rests on one critical factor: the accuracy of the user's functional threshold values. The TSS model is entirely relative to an individual's current fitness level, as defined by their FTP and FThP.2 A study by Banister showed that even a small 4% error in the assumed threshold power can lead to an 8% error in the calculated TSS. This systematic error would then propagate through all subsequent calculations, rendering metrics like chronic load and the ACWR unreliable. Therefore, it is an absolute requirement that the system's onboarding process mandates the input of accurate, recently tested threshold values and includes periodic reminders for the athlete to re-test as their fitness changes.

### **Section 3: Proactive Injury Risk Mitigation via the Acute:Chronic Workload Ratio (ACWR)**

#### **3.1 The Fitness-Fatigue Model and ACWR**

The Acute:Chronic Workload Ratio (ACWR) is a powerful, evidence-based tool for monitoring training load to mitigate injury risk. It is a practical application of Banister's impulse-response model, which posits that every workout generates both a positive "fitness" impulse and a negative "fatigue" impulse. The ACWR quantifies the relationship between these two states.

* **Acute Training Load (ATL):** This represents the athlete's current fatigue. It is the cumulative training load (measured in UTL) from the most recent 7-day period.  
* **Chronic Training Load (CTL):** This represents the athlete's current fitness or preparedness. It is the rolling average training load over a longer period, typically the last 28 to 42 days.  
* The Ratio: The ACWR is calculated by dividing the acute load by the chronic load:

  ACWR=CTLATL​

#### **3.2 Interpreting the Ratio: The "Sweet Spot" and "Danger Zone"**

Research has established clear, actionable thresholds for interpreting the ACWR, which can guide training decisions to optimize adaptation while minimizing risk.

* **Undertraining/Detraining (ACWR \< 0.8):** An athlete in this zone is likely losing fitness. While the immediate injury risk is low, a prolonged period of undertraining can increase the risk of future injury when training load is eventually increased again.  
* **The "Sweet Spot" (0.8 ≤ ACWR ≤ 1.3):** This is considered the optimal training zone. Athletes training within this range are progressively building fitness while keeping their risk of injury relatively low. This zone allows for adequate stress to stimulate adaptation without overwhelming the body's recovery capacity.  
* **The "Danger Zone" (ACWR ≥ 1.5):** When the acute load significantly outpaces the chronic load, injury risk increases dramatically. Studies have shown that an ACWR above 1.5 can increase the risk of a non-contact, overuse injury by two to four times in the subsequent week. The range between 1.3 and 1.5 serves as a cautionary "orange zone" where risk begins to climb.

#### **3.3 Calculation Methodology: EWMA vs. Rolling Average**

The ATL and CTL can be calculated using a simple rolling average (e.g., the sum of the last 7 days divided by the average of the last 28 days). However, a more sophisticated and sensitive method is the **Exponentially Weighted Moving Average (EWMA)**. The EWMA gives greater weight to more recent training sessions, better reflecting the decaying nature of fitness and fatigue. For example, a workout done yesterday has a greater impact on today's fatigue than a workout done seven days ago. Studies have shown that an ACWR calculated using the EWMA model is more sensitive and demonstrates a stronger correlation with the occurrence of non-contact injuries compared to the simple rolling average method. For this reason, the proposed system will utilize the EWMA for calculating both ATL and CTL.

#### **3.4 Nuances and Criticisms of the ACWR Model**

While the ACWR is a valuable tool recommended by bodies like the International Olympic Committee, it is essential to acknowledge its limitations to build a responsible application. Critics have pointed out that the specific time windows (7 and 28 days) are somewhat arbitrary and that the model is a measure of *training load*, not a direct measure of the *mechanical load* being placed on specific tissues.

Crucially, the ACWR is a probabilistic tool that identifies an *association* with increased injury risk; it is not a deterministic predictor of injury at the individual level. A high ACWR is a strong "red flag," not a guarantee of impending injury. The system must therefore present this information as a risk management guide, not an absolute diagnosis.

A critical point of understanding is that the ACWR model does not penalize high training loads. On the contrary, research demonstrates that a high chronic training load—representing a high level of fitness—is protective against injury. The danger arises not from the absolute load, but from the *rate of change* of that load. A rapid spike in training that the body is not prepared for is what elevates risk. The primary function of the ACWR module within the algorithm is therefore not to keep an athlete's training load low, but to act as a governor on the *ramp rate*, ensuring that fitness (CTL) is built progressively and safely, without dangerous spikes in fatigue (ATL).

Furthermore, the standard 0.8-1.3 "sweet spot" represents a population average. For an athlete with a significant history of overuse injuries, such as stress fractures or chronic tendonitis, these thresholds may be too aggressive. To truly personalize the protocol, the system must incorporate user-provided injury history. If an athlete indicates a history of such injuries, the system should engage a "conservative mode," tightening the acceptable ACWR boundaries (e.g., to a maximum of 1.2) to provide an additional margin of safety. This directly translates a qualitative user input into a quantitative algorithmic constraint, making the system adaptive and individual-centric.

### **Section 4: Autonomic Readiness: Leveraging Heart Rate Variability (HRV)**

#### **4.1 HRV as a Proxy for Autonomic Nervous System (ANS) State**

While the ACWR provides a medium-term view of injury risk based on accumulated load, Heart Rate Variability (HRV) offers a real-time, daily snapshot of an athlete's physiological readiness to train. HRV is the measure of the natural variation in the time interval between consecutive heartbeats. This variation is controlled by the Autonomic Nervous System (ANS), which consists of two main branches:

* **Sympathetic Nervous System (SNS):** The "fight or flight" system, which prepares the body for action and stress.  
* **Parasympathetic Nervous System (PNS):** The "rest and digest" system, which promotes recovery and relaxation.

A healthy, well-recovered athlete will exhibit high parasympathetic activity at rest, resulting in a higher HRV. This indicates that the body is prepared to handle stress. Conversely, after a hard workout, or during periods of high life stress, illness, or poor sleep, sympathetic activity increases and parasympathetic activity is withdrawn. This leads to a more regular, metronomic heartbeat and thus a lower HRV, signaling that the body is in a stressed state and may not be ready for another high-intensity training session.

#### **4.2 The Primary Metric: RMSSD**

Of the various metrics used to quantify HRV, the **Root Mean Square of Successive Differences (RMSSD)** is the gold standard for daily athlete monitoring. RMSSD is a time-domain measurement that specifically reflects vagal (parasympathetic) activity and has been shown to be less influenced by breathing rate compared to frequency-domain metrics like High Frequency (HF) power. Because HRV data is not normally distributed, it is standard practice to use the natural logarithm of RMSSD (lnRMSSD) for statistical analysis and establishing baselines.

#### **4.3 The HRV-Guided Training Protocol**

An effective HRV-guided training protocol is built on a simple but powerful premise: compare today's reading to the athlete's own recent history to determine readiness for intensity.

* **Establishing a Baseline:** A personalized baseline is essential, as there is no universal "good" RMSSD value. Best practice, supported by numerous studies, is to establish a **7- to 10-day rolling average** of morning lnRMSSD readings. This moving average allows the baseline to adapt as the athlete's fitness changes over time.  
* **Daily Measurement Protocol:** Consistency is paramount for reliable HRV data. Measurements must be taken at the same time each day, typically immediately upon waking, and in the same body position (e.g., sitting or standing). A validated heart rate sensor (preferably a chest strap) and application should be used.  
* **Interpreting Daily Fluctuations (The Threshold Logic):** The core of the protocol is the daily decision logic. The system compares the daily lnRMSSD value to the statistical range of the rolling baseline. A common and effective method is to define a "normal range" using the mean and standard deviation (SD) of the 7-day baseline.  
  * If the daily lnRMSSD is **within or above** the normal range (e.g., greater than the mean minus 0.5 SD), the athlete's ANS is considered balanced and recovered. They are cleared to perform the planned training, including high-intensity sessions.  
  * If the daily lnRMSSD is **significantly below** the normal range (e.g., less than the mean minus 1.0 SD), it indicates that the athlete is in a state of physiological stress. The protocol then prescribes a modification to the planned training, typically replacing a high-intensity session with a low-intensity workout or a complete rest day.

#### **4.4 Evidence and Efficacy**

Multiple meta-analyses have examined the effectiveness of HRV-guided training. The consensus is that while it may only provide a small advantage over well-designed predefined plans in terms of group-level performance improvements, its primary benefits lie elsewhere. HRV-guided training has been shown to be superior for enhancing vagal tone (a key marker of cardiovascular health), reducing the likelihood of negative training responses, and promoting more consistent positive adaptations at the individual level. By providing an objective measure of daily recovery, it serves as a powerful tool to prevent non-functional overreaching and reduce time lost to illness and injury.

The intervention prescribed by HRV-guided protocols is specific: it primarily governs the application of *intensity*. A low HRV reading is a "no-go" signal for high-intensity stress; it is not necessarily a command to cease all activity. The appropriate algorithmic response to a suppressed HRV is to modify the day's training recommendation by capping the intensity, guiding the athlete towards a low-intensity, recovery-focused session rather than complete rest, unless HRV has been suppressed for multiple consecutive days. This allows the athlete to continue accumulating training volume that aids recovery while avoiding the additional stress that could push them toward NFOR.

## **Part II: The Athlete Data Ecosystem: Leveraging the Garmin API**

### **Section 5: Accessing the Athlete's Physiological Data Stream**

#### **5.1 The Garmin Connect Developer Program**

To power the algorithms described in Part I, the system requires access to a rich stream of physiological and activity data. The Garmin ecosystem is the designated source for this data. Integration will be achieved through the **Garmin Connect Developer Program**, which provides a collection of cloud-to-cloud APIs for accessing user data. It is important to note that access to this program is typically granted to approved businesses and is not intended for personal hobbyist projects, a key consideration for the development and deployment strategy.

#### **5.2 Required APIs**

The system will rely on two primary APIs within the Garmin Connect Developer Program:

* **Health API:** This API is the source for all-day health and wellness metrics. It provides daily summaries of key data points that are essential for assessing an athlete's recovery and readiness status. Crucially, this includes daily HRV summaries, resting heart rate, detailed sleep data, and all-day stress levels.3  
* **Activity API:** This API provides access to the detailed data files recorded during training sessions. It allows for the download of activity files in their native Flexible and Interoperable Data Transfer (.FIT) format, as well as.TCX and.GPX formats.4 Access to the raw.FIT file is a requirement, as it contains the second-by-second data streams (e.g., power, pace, heart rate) needed for the accurate calculation of UTL scores.

#### **5.3 Data Flow and Authentication**

The integration will follow a standard, secure workflow. A new user will register for the service and then be directed through an OAuth 2.0 authentication flow. During this process, the user will grant the application explicit permission to access their Garmin Connect data. Once consent is granted, the application's backend server can communicate with Garmin's servers to retrieve data. The Health API supports both a "push" model, where Garmin sends a notification when new data is available, and a "ping/pull" model, where the application's server periodically queries for new data. A daily pull of the previous day's data is the most straightforward implementation for this system's requirements.

### **Section 6: Mapping Key Garmin Data Points to the Protocol Engine**

#### **6.1 Health API Data Fields for Readiness Assessment**

The daily readiness assessment, driven primarily by the HRV-guided protocol, will be fueled by specific data fields from the Health API. The data is delivered in JSON format and contains the following critical metrics:

* **HRV Summaries:** This is the most critical data point for the readiness algorithm. The Health API provides a daily summary object that includes hrvStatus (e.g., "Unbalanced", "Balanced"), the lastNightAvg RMSSD value in milliseconds, and the baseline (7-day average) RMSSD value. These fields directly map to the inputs required for the HRV-guided logic defined in Section 4\.  
* **Sleep Summaries:** The API provides dailySleepDTO which includes sleepStartTimestamp, sleepEndTimestamp, and total duration in seconds. It also provides durations for deepSleepSeconds, lightSleepSeconds, and remSleepSeconds. This data will serve as a powerful secondary indicator of recovery. A low HRV reading accompanied by a record of poor sleep provides strong justification for a recommended recovery day.  
* **Resting Heart Rate:** The restingHeartRate field provides the daily resting heart rate in beats per minute. This will be used as an input for the Banister's TRIMP calculation and can also be tracked over time as a long-term marker of fitness or overtraining.  
* **Stress Summaries:** The averageStressLevel (a score from 0-100) and stressDurationSeconds provide insight into the total physiological stress experienced by the athlete, including non-training life stress. This contextualizes the overall recovery picture.

#### **6.2 Activity FIT File Data Fields for Load Calculation**

To calculate the Unified Training Load (UTL), the system must ingest and parse the raw.FIT files provided by the Activity API. This requires a robust FIT file parser, for which several open-source Python libraries exist (e.g., fitdecode, python-fitparse). The parser must be capable of extracting data from several key FIT message types.

* **session Message:** This message provides summary data for the entire activity. Key fields include sport, sub\_sport, total\_elapsed\_time, total\_timer\_time, total\_distance, and, importantly, device-calculated summary fields like avg\_power, normalized\_power, and training\_stress\_score.  
* **record Message:** This is the most critical message type, containing the time-series data recorded throughout the activity. These messages are typically recorded every second. The algorithm will iterate through these messages to access the following fields:  
  * For Cycling TSS: timestamp, power (watts), heart\_rate (bpm), cadence (rpm), speed (m/s).  
  * For Running rTSS: timestamp, enhanced\_speed (m/s), heart\_rate (bpm), cadence (spm), altitude (m).  
* **lap Message:** Provides summary data for each lap or split within the activity.  
* **Running Dynamics:** For users with compatible accessories (e.g., HRM-Pro, Running Dynamics Pod), the record messages may also contain running dynamics fields such as ground\_contact\_time, vertical\_oscillation, and stride\_length. While not used directly in the UTL calculation, this data should be stored and can be presented to the user for gait analysis.

A critical initial step in processing any new activity file is a data completeness and quality check. The algorithm's logic must mirror the accuracy hierarchy established in Section 2.4. Upon receiving a new activity, the system must first inspect the available data streams. If it is a cycling activity, it will check for the presence of a power field in the record messages. If present, it will proceed with a power-based TSS calculation. If absent, it will fall back to checking for a heart\_rate stream to perform a TRIMP/hrTSS calculation. This fault-tolerant approach ensures that every activity receives a load score, while always prioritizing the most accurate method available.

Furthermore, modern Garmin devices perform their own onboard calculations and store valuable metrics within the FIT file, such as total\_training\_effect, total\_anaerobic\_training\_effect, and training\_load\_peak (an EPOC-based load score). While the system will rely on its own consistent UTL calculations, these native Garmin metrics provide an invaluable opportunity for a "sanity check." The system can compare its calculated UTL score with Garmin's training\_load\_peak. A significant and persistent discrepancy between the two could indicate a misconfigured threshold value in the user's profile, triggering a notification for the user to review and potentially re-test their FTP or FThP.

#### **6.3 Table 1: Required Garmin API Data Fields and Their Application**

The following table synthesizes the data requirements, linking specific data points from the Garmin API to their precise function within the training protocol's algorithms.

| Data Point | API Source | Data Type | Algorithmic Purpose | Snippet Reference |
| :---- | :---- | :---- | :---- | :---- |
| Nightly RMSSD | Health API | integer (ms) | Primary input for daily HRV readiness calculation. |  |
| 7-Day Avg RMSSD | Health API | integer (ms) | Establishes the rolling baseline for HRV readiness. |  |
| Resting Heart Rate | Health API | integer (bpm) | Secondary readiness/fitness marker; input for TRIMP calculation. |  |
| Sleep Duration | Health API | integer (sec) | Contextual data for readiness; flags poor recovery. |  |
| Activity FIT File | Activity API | .fit (binary) | Raw data source for all workout-specific calculations. | 4 |
| Power (Record Msg) | FIT File | integer (watts) | Primary input for cycling TSS calculation. |  |
| Enhanced Speed (Record Msg) | FIT File | float (m/s) | Primary input for running rTSS calculation (Pace). |  |
| Heart Rate (Record Msg) | FIT File | integer (bpm) | Primary input for fallback TRIMP/hrTSS calculation. |  |
| Altitude (Record Msg) | FIT File | float (m) | Input for Normalized Graded Pace (NGP) algorithm in rTSS. |  |
| Timestamp (Record Msg) | FIT File | datetime | Used to calculate duration and link all time-series data. |  |

## **Part III: Product Requirements Document (PRD): The "TrainSmart" Protocol Engine**

### **Section 7: Vision and Core Principles**

#### **7.1 Product Vision**

To be the most intelligent and scientifically-grounded training companion for multi-sport endurance athletes, providing daily, personalized training load recommendations that maximize performance gains while proactively minimizing the risk of overuse injuries.

#### **7.2 Core Principles**

* **Science First:** Every recommendation must be traceable to established physiological principles and peer-reviewed research. The system's logic is transparently based on the models of progressive overload, unified training stress, and ACWR.  
* **Individuality:** The system must adapt to the user's unique physiology, goals, and history. One-size-fits-all plans are explicitly rejected in favor of a dynamic, N-of-1 approach.  
* **Proactive, Not Reactive:** The primary goal is injury prevention through intelligent load management, not just performance tracking. The system is designed to anticipate and mitigate risk before it leads to a training disruption.  
* **Data-Driven:** All decisions are made algorithmically based on objective data from the user's Strava account. Subjective feelings are acknowledged but do not override objective physiological markers when making load recommendations.

### **Section 8: User Profile, Onboarding, and Baselines**

#### **8.1 User Registration and Garmin Authentication**

The user will create an account using a standard email and password. Immediately upon registration, the user will be prompted to connect their Garmin Connect account. This is a mandatory step, as the application cannot function without a data source. The connection will be established via a secure OAuth 2.0 flow, where the user explicitly grants the application read-only access to their Health and Activity data.

#### **8.2 Initial User Input**

Upon successful authentication, the user will complete a one-time onboarding questionnaire to provide essential personalization data:

* **Demographics:**  
  * Age (Years)  
  * Gender (Male/Female) \- Used for Banister's TRIMP formula selection.  
  * Weight (kg or lbs) \- Used for calculating power-to-weight ratio and other potential metrics.  
* **Injury History:**  
  * A multi-select checklist of common overuse injuries, including but not limited to: Plantar Fasciitis, Achilles Tendonitis, Shin Splints (MTSS), IT Band Syndrome, Runner's Knee (PFPS), and Stress Fractures.  
  * Selection of one or more of these options will automatically enable the "Conservative Mode" for ACWR thresholds, narrowing the "sweet spot" to 0.8-1.2.  
* **Event Goals:**  
  * The user must be able to add one or more target events.  
  * For each event, they must specify:  
    * Event Name (e.g., "Chicago Marathon")  
    * Sport (Running, Cycling, Duathlon, Triathlon)  
    * Event Type/Distance (e.g., 10k, Half Marathon, Marathon, 50-mile Gravel Race, Century Ride, etc.)  
    * Event Date

#### **8.3 Physiological Baseline Establishment**

This is the most critical phase of onboarding. The system's accuracy is entirely dependent on valid physiological baselines.

* **Threshold Testing:** The user will be guided to input their current physiological thresholds. The UI will strongly emphasize the importance of these values for accurate load calculation.  
  * **Cycling:** Functional Threshold Power (FTP) in watts.  
  * **Running:** Functional Threshold Pace (FThP) in min/mile or min/km.  
  * **Heart Rate:** Maximum Heart Rate (Max HR) and Resting Heart Rate (RHR) in bpm.  
  * The application will provide links to standardized field test protocols (e.g., 20-minute FTP test, 30-minute run test) to help users determine these values accurately.  
* **HRV Baseline Period:** After completing the profile, the system will enter an initial 10-day HRV baseline establishment period.  
  * The user will be instructed to take a daily morning HRV reading using their Garmin device.  
  * During this period, daily training recommendations will be generated, but they will be based solely on a conservative ACWR progression model. HRV-based modifications will be disabled.  
  * The UI will display a countdown (e.g., "7 days of HRV data remaining to unlock full personalization") to encourage compliance. After 10 consecutive days of readings, the HRV-guided features will be fully activated.

### **Section 9: The Core Algorithm: From Raw Data to Daily Recommendation**

The core of the product is a daily-executed algorithm that synthesizes all available data into a single, actionable training load recommendation.

#### **9.1 Step 1: Daily Data Ingestion and Processing**

This process will run automatically once per day for each user (e.g., at 4:00 AM in their local timezone).

1. **Fetch Health Data:** Make a call to the Garmin Health API to retrieve the user's health summary for the previous day. This includes the latest nightly RMSSD, sleep data, and resting heart rate.  
2. **Fetch Activity Data:** Make a call to the Garmin Activity API to check for any new activities completed since the last sync.  
3. **Process Activities:** For each new activity file:  
   * Download the.FIT file.  
   * Parse the file to extract relevant data streams.  
   * Execute the UTL calculation logic from Section 2.4, using the hierarchical model (Power TSS \> Pace rTSS \> HR-based TRIMP).  
   * Store the calculated UTL score and all relevant raw and summary data in the application's database, linked to the user and activity.

#### **9.2 Step 2: Update Long-Term Metrics**

1. **Recalculate Load Averages:** Using the new daily UTL scores, update the user's Acute Training Load (ATL) and Chronic Training Load (CTL) values. These will be calculated using an EWMA formula with time constants of 7 days for ATL and 42 days for CTL.  
   * ATLtoday​=(UTLtoday​×αATL​)+(ATLyesterday​×(1−αATL​)), where αATL​=2/(7+1)  
   * CTLtoday​=(UTLtoday​×αCTL​)+(CTLyesterday​×(1−αCTL​)), where αCTL​=2/(42+1)  
2. **Calculate ACWR:** Compute the current ACWR by dividing the updated ATL by the updated CTL.

#### **9.3 Step 3: Assess Daily Readiness**

1. **Retrieve HRV Data:** Access the latest morning lnRMSSD reading from the ingested health data.  
2. **Compare to Baseline:** Compare this value to the user's 7-day rolling mean and standard deviation of lnRMSSD.  
3. **Assign Readiness State:** Categorize the user's daily readiness into one of three states:  
   * **GREEN (Ready for Intensity):** daily\_lnRMSSD ≥ (baseline\_mean \- 0.5 \* baseline\_SD)  
   * **AMBER (Proceed with Caution):** (baseline\_mean \- 1.0 \* baseline\_SD) ≤ daily\_lnRMSSD \< (baseline\_mean \- 0.5 \* baseline\_SD)  
   * **RED (Recovery Recommended):** daily\_lnRMSSD \< (baseline\_mean \- 1.0 \* baseline\_SD)

#### **9.4 Step 4: The Recommendation Engine (Decision Logic)**

This final step integrates the user's long-term plan, medium-term injury risk (ACWR), and short-term readiness (HRV) to generate the daily recommendation.

1. **Determine Planned Load:** Based on the user's event goals and current training phase (e.g., base, build, peak, taper), the system calculates a target weekly UTL designed to produce a gradual increase in CTL (e.g., \+3 to \+5 CTL points per week in a build phase). This target is broken down into a "planned" daily UTL.  
2. **Apply Decision Matrix:** The system uses the logic defined in Table 2 to modify the planned load based on the current ACWR and HRV state.  
3. **Generate Output:** The final output presented to the user consists of:  
   * A target **UTL number** for the day (e.g., "Today's Target Load: 95").  
   * A qualitative **readiness summary** (e.g., "Your HRV is in the normal range, and your training load is well-managed. You are cleared for high-intensity training.").  
   * A suggested **modality split** (e.g., "Recommendation: 95 UTL Run OR 95 UTL Bike OR a combination like a 50 UTL Run \+ 45 UTL Bike.").

#### **9.5 Table 2: The Recommendation Engine Decision Matrix**

This matrix forms the logical core of the recommendation engine, defining the explicit rules that govern every daily output.

| ACWR Zone | HRV Readiness | Resulting Action | Target UTL | Intensity Allowed |
| :---- | :---- | :---- | :---- | :---- |
| Danger (≥1.5) | Any | Forced Recovery | \< 40% of Daily Avg | Low Only (Z1/2) |
| Any | RED (Recovery) | Forced Recovery | \< 40% of Daily Avg | Low Only (Z1/2) |
| Caution (1.3-1.5) | AMBER or GREEN | Maintain/Reduce Load | ≤ ATL/7 | Low/Moderate (No HIIT) |
| Sweet Spot (\<1.3) | AMBER (Caution) | Maintain/Reduce Load | ≤ ATL/7 | Low/Moderate (No HIIT) |
| Sweet Spot (\<1.3) | GREEN (Ready) | Proceed as Planned | Follow Long-Term Plan | All Intensities Allowed |

### **Section 10: Functional Requirements and User Stories**

#### **10.1 Athlete Stories**

* **FR-1:** As an athlete, I want to connect my Garmin account during onboarding so the app can automatically import all my training data.  
* **FR-2:** As an athlete, I want to input my goals, like an upcoming marathon, so the system can create a long-term plan for me.  
* **FR-3:** As an athlete with a history of shin splints, I want to tell the app about my injury history so it can provide more cautious recommendations.  
* **FR-4:** As an athlete, I want to see a single, clear number on my dashboard each day that tells me how much training load I should aim for.  
* **FR-5:** As an athlete, I want to receive a clear warning when my training load is increasing too quickly so I can prevent an overuse injury.  
* **FR-6:** As an athlete, I want the system to tell me to take an easy day or rest when my body is not recovered, based on my morning HRV reading.  
* **FR-7:** As an athlete, I want to use a planner to schedule my workouts for the upcoming week and see how my plan will affect my future training load and injury risk.

#### **10.2 System Requirements**

* **SR-1:** The system must implement a secure OAuth 2.0 client to authenticate with the Garmin Connect API.  
* **SR-2:** The system must include a FIT file decoder capable of parsing session, lap, and record messages for running and cycling activities.  
* **SR-3:** The system must implement algorithms to calculate power-based TSS, pace-based rTSS, and heart rate-based TRIMP.  
* **SR-4:** The system must store historical time-series data for all relevant user metrics in a relational or time-series database.  
* **SR-5:** The recommendation algorithm must be executed via an automated daily cron job for all active users.  
* **SR-6:** The system must maintain a rolling 7-day baseline of lnRMSSD for each user to facilitate daily HRV analysis.

### **Section 11: Data Model and API Integration Specification**

#### **11.1 Database Schema (Simplified)**

* **Users Table:**  
  * user_id (PK), email, password_hash, age, gender, weight, strava_user_id, strava_oauth_token, injury_history_flags (JSON or bitmask).  
* **Thresholds Table:**  
  * threshold_id (PK), user_id (FK), ftp_watts, fthp_mps, max_hr, resting_hr, date_updated.  
* **Activities Table:**  
  * activity_id (PK), user_id (FK), strava_activity_id, start_time, sport, duration_sec, distance_m, UTL_score, calculation_method (e.g., 'TSS', 'rTSS', 'TRIMP'), raw_fit_file_path.  
* **Training_Load_Metrics Table:**  
  * metric_id (PK), user_id (FK), calendar_date, daily_UTL, ctl, atl, acwr.

#### **11.2 API Integration Specification**

* **Strava API Endpoints:**  
  * GET /strava/api/activities: To retrieve a list of new activities.  
  * GET /strava/api/activities/{id}/download: To download the raw.FIT, .TCX, or .GPX file for a specific activity.  
* **Error Handling:** The integration must handle potential API errors, such as rate limiting (429), unauthorized (401), and server errors (5xx).  
* **Data Backfilling:** For a new user, the system must include a mechanism to backfill at least 90 days of historical activity data from Strava to establish initial CTL baselines.

### **Section 12: User Interface (UI) and Visualization Recommendations**

#### **12.1 The Dashboard (Home Screen)**

The dashboard is the primary user interaction point and must convey the daily recommendation with absolute clarity.

* **Primary Recommendation Card:** A large, prominent card at the top of the screen displaying:  
  * **Today's Target UTL:** e.g., "95".  
  * **ACWR Status:** A color-coded gauge or bar showing the current ACWR value (e.g., 1.1) within the context of the safe (green), caution (orange), and danger (red) zones, similar to the mytf.run interface.  
  * **Plain Language Summary:** A concise sentence explaining the "why" behind the recommendation, e.g., "Your training load is in the sweet spot. Today is a good day for a high-quality workout."

#### **12.2 The Planner View**

This view allows for proactive planning and is a key differentiator.

* **Calendar Interface:** A weekly or monthly calendar view. Past days show the completed UTL for each activity. Future days show the system's recommended UTL.  
* **Interactive Planning:** Users can click on a future day to schedule a specific workout (e.g., "Long Run \- 15 miles" or "Interval Ride \- 2x20 min @ FTP").  
* **Dynamic Forecasting:** As the user adds or modifies planned workouts, the system will estimate the UTL for those sessions and instantly recalculate and re-render the future ACWR forecast on the calendar. This provides immediate visual feedback, showing the user if their plan will push them into the danger zone, a core feature inspired by mytf.run.

#### **12.3 The Performance Chart**

This view provides the user with a macro-level perspective on their training progression over time.

* **Performance Management Chart:** A direct implementation of the classic fitness-fatigue model chart.  
  * The chart will plot three lines over a selectable time period (e.g., 6 weeks, 3 months, 1 year):  
    * **CTL (Fitness):** A blue line showing the long-term trend of fitness.  
    * **ATL (Fatigue):** A pink line showing short-term fatigue.  
    * **Training Stress Balance (TSB \= CTL \- ATL):** Yellow bars representing daily form or readiness. Positive TSB indicates good form, while negative TSB indicates fatigue.  
  * This chart gives the user a powerful visual tool to understand their training cycles, see how their fitness is building, and plan for periods of peak form for their target events.

#### **Works cited**

1. Training load and training stress scores for runners. \- Veohtu, accessed on September 3, 2025, [https://www.veohtu.com/trimp.html](https://www.veohtu.com/trimp.html)  
2. The Science of the TrainingPeaks Performance Manager, accessed on September 3, 2025, [https://www.trainingpeaks.com/learn/articles/the-science-of-the-performance-manager/](https://www.trainingpeaks.com/learn/articles/the-science-of-the-performance-manager/)  
3. Health API | Garmin Connect Developer Program | Garmin Developers, accessed on September 3, 2025, [https://developer.garmin.com/gc-developer-program/health-api/](https://developer.garmin.com/gc-developer-program/health-api/)  
4. Activity API | Garmin Connect Developer Program | Garmin Developers, accessed on September 3, 2025, [https://developer.garmin.com/gc-developer-program/activity-api/](https://developer.garmin.com/gc-developer-program/activity-api/)