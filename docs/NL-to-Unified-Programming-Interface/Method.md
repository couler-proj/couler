In this file, we introduce the application of LLMs for converting Natural Language (NL) to Unified Programming Interface. Traditional methods involve defining workflows using various techniques and submitting them to a cluster. Lately, LLMs have demonstrated remarkable performance across a wide array of inference tasks. However, upon direct application of LLMs for unified programming code generation, certain challenges arise: Firstly, the overall workflow complexity hampers the performance of LLMs in complete workflow conversion. Secondly, LLMs possess limited knowledge regarding Couler's unified programming interface.

To address these challenges, we introduce a method that leverages LLMs to automatically translate natural language into unified programming code via the crafting of task-specific prompts. This approach enables users to articulate their desired workflows in natural language, which are then automatically translated into executable unified programming code. As a result, our method simplifies the Couler workflow creation process and improves usability for individuals with limited programming experience. The transition from NL descriptions to Couler code encompasses four pivotal steps:

**Step 1: Modular Decomposition:** 

Initially, we employ a chain of thought strategy to decompose natural language descriptions into smaller, more concise task modules, such as data loading, data processing, model generation, and evaluation metrics. Each module should encapsulate a singular, coherent task to ensure the precision and correctness of the generated Couler code. A series of predefined task types can be established to identify and extract pertinent tasks based on the input of natural language descriptions automatically. They provide a structured approach to ensure the precision and correctness of the code generated.

**Step 2: Code Generation:** 

For each independent subtask, we utilize LLMs to generate code. Considering that LLMs have limited knowledge about Couler, we construct a Code Lake containing code for various functions. We search for relevant code from the Code Lake for each subtask and provide it to LLMs for reference. This significantly improves the ability for unified programming code generation.

**Step 3: Self-calibration:** 

After generating the code for each subtask, we integrate a self-calibration strategy to optimize the generated code. This strategy evaluates the generated code by having LLMs critique it. Initially, we define a baseline score  as the standard evaluation score. We use LLMs to evaluate the generated code for a score between 0 and 1, and if, we will provide feedback of LLMs and repeat the code generation. After this self-calibration, we will have improved code for each subtask.

**Step 4: User Feedback:** 

Finally, users can review and validate the generated workflow code. If the generated code fails to meet the users' requirements, they have the opportunity to provide feedback and suggestions in textual format. The system will leverage this feedback to optimize the code and enhance the precision of code generation.


