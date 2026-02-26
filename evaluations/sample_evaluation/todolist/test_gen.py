# generates test scenarios for the todolist assignment

from src.grader.grader import Grader
from src.utils import in_executor

grader = None

RANDOM_TASKS = [
    "buy groceries",
    "call mom",
    "finish homework",
    "clean the house",
    "pay bills",
    "go for a run",
    "read a book",
    "write a blog post",
    "plan a trip",
    "organize the garage",
    "join computing club",
    "learn a new programming language",
]

def set_grader(g: Grader) -> None:
    """Set the grader instance for test generation."""
    global grader
    grader = g

def obfuscate_task(task: str) -> str:
    """Obfuscate a task by randomly capitalizing letters."""
    obfuscated = ""
    for char in task:
        if char.isalpha() and grader.get_random_int(0, 100) < 50:
            obfuscated += char.upper()
        else:
            obfuscated += char
    return obfuscated


@in_executor
def generate_test(output_txt: str, length: int) -> None:
    """Generate a test scenario for the todolist assignment."""
    tasks = []
    for _ in range(length):
        task = grader.get_random_choice(RANDOM_TASKS)
        obfuscated_task = obfuscate_task(task)
        tasks.append(obfuscated_task)

    with open(output_txt, "w") as test_file:
        add_random_newline = grader.get_random_int(0, 100) < 30
        for task in tasks:
            test_file.write(task + "\n")
            if add_random_newline and grader.get_random_int(0, 100) < 20:
                test_file.write("\n") # Add random extra newlines for complexity

@in_executor
def generate_solution(input_txt: str) -> None:
    """Generate a test scenario for the todolist assignment."""
    with open(input_txt) as todofile, open(input_txt.split(".")[0] + "_sol.txt", "w") as outputfile:
        items = todofile.readlines()

        outputfile.write("To-do list\n\n")
        for item in items:
            if item.strip() != "":
                item = item.lower()
                formatted_item = "- " + item[0].capitalize() + item[1:]
                outputfile.write(formatted_item)

async def orchestrate_test_generation(output_txt: str, length: int) -> dict:
    """Orchestrate the test generation process."""
    await generate_test(output_txt, length)
    await generate_solution(output_txt)

    return {
        "output_test_file": output_txt,
        "output_sol_file": output_txt.split(".")[0] + "_sol.txt"
    }
