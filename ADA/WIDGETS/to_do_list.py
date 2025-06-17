def create_list():
    """
    Creates an empty to-do list.

    Returns:
        list: An empty to-do list.
    """
    return []

def add_task(todo_list, task):
    """
    Adds a task to the to-do list.

    Args:
        todo_list (list): The to-do list.
        task (str): The task to add.
    """
    todo_list.append(task)
    print(f"Task '{task}' added to the to-do list.")

def delete_task(todo_list, task):
    """
    Deletes a task from the to-do list.

    Args:
        todo_list (list): The to-do list.
        task (str): The task to delete.
    """
    if task in todo_list:
        todo_list.remove(task)
        print(f"Task '{task}' removed from the to-do list.")
    else:
        print(f"Task '{task}' not found in the to-do list.")

def display_todo_list(todo_list):
    """
    Displays the current to-do list.

    Args:
        todo_list (list): The to-do list.
    """
    if not todo_list:
        print("Your to-do list is empty.")
    else:
        print("Your to-do list:")
        for i, task in enumerate(todo_list):
            print(f"{i+1}. {task}")

if __name__ == "__main__":
    my_todo_list = create_list()
    add_task(my_todo_list, "Grocery Shopping")
    add_task(my_todo_list, "Pay Bills")
    add_task(my_todo_list, "Walk the Dog")
    display_todo_list(my_todo_list)
    delete_task(my_todo_list, "Pay Bills")
    display_todo_list(my_todo_list)
