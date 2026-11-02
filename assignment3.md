# Assignment 3: Interaction and Evaluation

## Task 1: Implementing interaction (20%)

**Visualization 1: Distance vs. Commute Time by Transport Mode (Scatterplot)**
Static version: A single scatterplot of distance versus commute time, with each trip colored by transport mode. It shows the general trend (longer trips take longer) and lets viewers see every individual trip. Because many trips cluster at similar distances and times, points overlap, which makes it hard to compare modes within a specific distance range or judge how consistent each mode’s commute times are.

/insert image here/

Interactive version: The same scatterplot, with the same colors and data, plus three interactions:

- Brushing and linking (the main interaction): Viewers drag across a distance range on the scatterplot, and a linked chart shows the average commute time, spread (±1 standard deviation), and trip count for each mode within that range. This replaces eyeballing overlapping dots with a direct comparison of modes at similar distances.
- Legend selection: Clicking a mode in the legend isolates it in both charts and fades the others, so viewers can focus on one mode at a time.
- Details on demand: Hovering over a point shows its day, weather, location, distance, and duration, and hovering over a summary bar shows its mean, standard deviation, and trip count.

/insert images here/

Why we expect it to help: Our analytical question is whether some modes, such as trains, have more predictable commute times than others, such as cars. That is a question about spread at comparable distances, which is hard to read from overlapping points. Brushing lets a viewer fix the distance range and compare average and spread across modes directly, so we expect faster and more accurate answers to tasks like “Which mode has the most consistent commute time for trips of 10-20 miles?”

**Visualization 2: Average Commute Time by Day of the Week (Bar Chart)**
Static Version: A standard bar chart showing the overall average commute time for Monday through Friday.

/ insert visualization here /

Interactive Version: added filtering via a grouped bar chart and interactive legend. Users can click on a transportation mode in the legend (e.g., "Car") to remove the other modes from the chart. This allows them to see if a bad commute day (like Monday) is driven by car traffic, or if it affects trains and buses equally.

/ insert visualization here /

## Task 2: Evaluation design (20%)

Starter:

1. Define an evaluation question and corresponding hypothesis.
2. Come up with two analytical tasks with two variants, at least four questions total
3. Meausrements for each question
4. Balancing approahces for how to spearate by user
5. the full procedure we will use in task 3
6. also comopute expecvted answers or something
7. idk imma look at this more in depth later tonight trust

## Task 3: Conducting the evaluation (25%)

## Task 4: Quantitative analysis (25%)

## Task 5: Reflection and recommendations (10%)

## Extra Credit: Interactive Prototype using Curio
