# Eval Feature

Purpose: Able to run experiments to evaluate the query response of one against the other consistently. The user sets up an experiment and then pastes in the results, which will generate a prompt for the eval. The data will all be stored in the DB, but it's not connected to any of our corpus (works) or chunks.

Flow:
1. "Eval" page (linked from left nav):
    * Page has: 
        * CTA: "New Experiment" Button
        * Table: "Experiments" table that shows experiments created and the ability to click into them (#3)
2. "New Experiment" page
    * Setup new experiment:
        * Name experiment
        * answer_x description
        * answer_y description
        * Model used for answer_x - Manually typed out
        * Model used for answer_y - Manually typed out 
        * Model used as judge - Manually typed out
        * Select evaluation template (new template using existing pattern for prompt templates) -- eval_template
        * Add eval criteria dimensions:
            * The eval will generate a JSON like the following example:
            ```
            {
                "factual_correctness": <int>,
                "completeness": <int>,
                "coherence": <int>,
                "hallucination_risk": <int>,
                "academic_response": <int>,
                "overall_score": <int>,
                "justification": "Concise explanation referencing specific differences"
            }
            ```
            * The dimensions: factual_correctness, completeness, coherence, hallucination_risk, and academic_response are default, but can be customized or new ones added (overall_score and justification are always available)
            * The user can add, remove, or rename any dimension
            * In the db we'll store the dimension results in one table and the mapping of the name in another table
            * The results are numbers from -10 to 10:
                * +10  = Answer X is much better
                * +5  = Answer X is moderately better
                * +1  = Answer X is slightly better
                * 0  = No meaningful difference
                * -1  = Answer Y is slightly better
                * -5  = Answer Y is moderately better
                * -10  = Answer Y is much better


3. "Experiment" Page:
    * Name of experiment
    * Current results (answer_x vs. answer_y)
        * statistical analysis of experiments prompts -- comparing the evaluation of x and y across all dimensions
            * X win rate: P(score > 0)
            * Mean score
            * Median score
            * % tied
            * Harm rate: P(score < 0)        
        * Statistical test: wilcoxon signed-rank on overall_score deltas for N > 1 on answers per prompt
    * Input for new new "Prompt Test" with a "Add" button--this adds a new prompt_experiment for the experiment and adds it it to the "Experiment Prompts" table
    * TABLE: "Experiment Prompts" table of previously added prompts, each entry links to new "Experiment Prompt Page"

4. "Experiment Prompt" Page
    * Prompt as inputted in #3
    * CTA: Add Answers:
        * Module pop-ups up with a text input to paste in answer_x and answer_y and save
        * answer_x gets randomly mapped to answer_a or answer_b (we keep track of the mapping in the DB)
        * answer_y gets put into answer_b or answer_a (opposite choice of above)
        * This random mapping is for blind evaluation
    * TABLE: "Prompt Evaluations" table that shows a list of added answers through CTA above. Each row has:
        * Button to copy the eval prompt (based on the eval_template that has answer_a and answer_b)
        * Button to paste the eval result JSON based on the prompt above -- answer_a and answer_b get mapped back to answer_x and answer_y based on the random assignment when we added answers
        * Button to go to a new page to see all the previous results for this experiment prompt
    