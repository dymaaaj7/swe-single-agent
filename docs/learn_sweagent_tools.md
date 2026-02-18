# Learning Guide: SWE-agent Tools and Code Understanding

> **For:** Beginners who want to understand how SWE-agent works with code  
> **Prerequisite:** Basic Python knowledge  
> **Reading time:** 20 minutes

---

## Table of Contents

1. [The Big Picture: What is SWE-agent?](#1-the-big-picture-what-is-swe-agent)
2. [Tools: The Agent's Hands and Eyes](#2-tools-the-agents-hands-and-eyes)
3. [How Code is Stored: Text vs Structure](#3-how-code-is-stored-text-vs-structure)
4. [Understanding Tree-sitter (The Secret Weapon)](#4-understanding-tree-sitter-the-secret-weapon)
5. [Why This Matters: Real Examples](#5-why-this-matters-real-examples)
6. [Summary: What We Learned](#6-summary-what-we-learned)

---

## 1. The Big Picture: What is SWE-agent?

Imagine you're helping a friend fix a broken Lego set over the phone. Your friend is in another room and can only do what you tell them to do.

**SWE-agent works the same way:**
- There's an **AI Agent** (like you on the phone)
- There's a **Computer** (like your friend in the other room)
- The agent gives **instructions** to the computer
- The computer **executes** those instructions and reports back

```
┌─────────────────────────────────────────────────────────────┐
│                     HOW SWE-AGENT WORKS                     │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────┐      Instructions       ┌───────────────┐ │
│  │ AI Agent    │  ─────────────────────▶ │ Computer      │ │
│  │ (The Brain) │                         │ (The Worker)  │ │
│  └─────────────┘                         └───────────────┘ │
│         ▲                                          │       │
│         │         Results / Output                 │       │
│         └──────────────────────────────────────────┘       │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### What Does the Agent Need to Do?

To fix code, the agent needs to:
1. **See** the code (read files)
2. **Search** for things (find functions, variables)
3. **Edit** the code (make changes)
4. **Test** the changes (run code)

But how does the agent tell the computer to do these things? That's where **tools** come in!

---

## 2. Tools: The Agent's Hands and Eyes

### What is a Tool?

A **tool** is like a command the agent can use. Think of it like special powers in a video game:

| Tool Name | What It Does | Video Game Analogy |
|-----------|--------------|-------------------|
| `view` | Read a file | X-ray vision to see through walls |
| `search_file` | Find text in a file | Treasure detector |
| `str_replace` | Edit code | Magic wand to change things |
| `run_tests` | Check if code works | Health meter checker |

### Example: Using a Tool

Let's see how an agent uses the `view` tool to read a file:

```python
# This is what the agent sends to the computer:
# "Please use the 'view' tool to look at this file"

view /home/user/my_project/hello.py
```

Here's what the computer does when it receives this command:

```python
# ============================================================
# TOOL: view
# PURPOSE: Read and display the contents of a file
# ============================================================

# Line 1: Import the sys module (system functions)
# This lets us access command-line arguments
import sys

# Line 2: Get the file path from the command arguments
# sys.argv[1] means "the first thing the user typed after the command"
# Example: If user typed "view hello.py", sys.argv[1] is "hello.py"
file_path = sys.argv[1]

# Line 3: Open the file in read mode ("r" means read)
# The 'with' statement automatically closes the file when done
with open(file_path, "r") as file:
    
    # Line 4: Read all the content from the file
    # .read() returns the entire file as one big string
    content = file.read()
    
    # Line 5: Print the content to the screen
    # This sends the file contents back to the agent
    print(content)
```

**What happened?**
1. Agent said: "view hello.py"
2. Computer ran the tool code above
3. Computer printed the file contents
4. Agent now "sees" what was in the file

### Another Example: The Search Tool

Now let's look at the `search_file` tool:

```python
# ============================================================
# TOOL: search_file
# PURPOSE: Find specific text inside a file
# ============================================================

# Line 1: Import the sys module for command-line arguments
import sys

# Line 2: Import regular expressions (regex) for pattern matching
# Regex is like a super-powered "find" that can find patterns
import re

# Line 3: Get the search term from command arguments
# Example: If user typed "search_file hello", search_term is "hello"
search_term = sys.argv[1]

# Line 4: Get the file path from command arguments
# Example: If user typed "search_file hello myfile.py", file_path is "myfile.py"
file_path = sys.argv[2]

# Line 5: Open the file for reading
with open(file_path, "r") as file:
    
    # Line 6: Read all lines into a list
    # Each line becomes an item in the list
    # Example: ["line 1\n", "line 2\n", "line 3\n"]
    lines = file.readlines()
    
    # Line 7: Loop through each line with its line number
    # enumerate adds a number (starting at 1) to each item
    # Example: (1, "line 1\n"), (2, "line 2\n"), etc.
    for line_number, line in enumerate(lines, 1):
        
        # Line 8: Check if the search term is in this line
        # 'in' checks if the text exists anywhere in the line
        if search_term in line:
            
            # Line 9: Print the line number and the line content
            # f"..." is an f-string that lets us insert variables
            # {line_number} becomes the actual number
            # {line.strip()} removes extra spaces and newlines from the end
            print(f"Line {line_number}: {line.strip()}")
```

**Example Usage:**
```
search_term = "hello"
file_content = [
    "print('world')",
    "print('hello there')",  # <-- Found here!
    "x = 5",
    "hello_world()"           # <-- Found here!
]

Output:
Line 2: print('hello there')
Line 4: hello_world()
```

---

## 3. How Code is Stored: Text vs Structure

### The Problem: Code is Just Text

When computers store code, they store it as **plain text** - just letters and numbers:

```
File on disk: my_code.py
Content: "d e f   c a l c u l a t e ( a ,   b ) : \n     r e t u r n   a   +   b"
         ↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑
         Just characters, like a .txt file!
```

**To the computer, code looks like this:**
```
def calculate(a, b):
    return a + b
```

**Not like this (what humans see):**
```
Function named "calculate"
├── Parameter: a
├── Parameter: b
└── Body: return a + b
```

### Why This is Hard for the Agent

Imagine trying to find all the verbs in a book, but you only have the raw letters - no spaces, no punctuation recognition, just letters.

That's what searching code is like without understanding its structure!

#### Example: Finding All Functions (The Hard Way)

**What the agent wants:** "Find all functions in this file"

**What the agent has to do with text search:**

```python
# ============================================================
# BAD WAY: Using text search (what SWE-agent does now)
# ============================================================

# Line 1: Read the entire file as one string
with open("my_code.py", "r") as f:
    text = f.read()

# Line 2: Split into lines
lines = text.split("\n")

# Line 3: Look for lines that start with "def "
# This is called a "heuristic" - a guess that works most of the time
for i, line in enumerate(lines, 1):
    # Check if line starts with "def " (function definition)
    if line.strip().startswith("def "):
        print(f"Found function at line {i}: {line}")

# PROBLEMS WITH THIS APPROACH:
# 1. What about "async def"? (missed!)
# 2. What about "# def fake_function()" in a comment? (false positive!)
# 3. What about functions inside classes vs module-level? (can't tell!)
# 4. What about decorators above the function? (missed!)
```

**Real-world problems:**

```python
# This would be WRONGLY detected as a function by text search:
# def this_is_just_a_comment()

# This would be MISSED by simple "startswith" search:
@decorator
async def my_async_function():  # Starts with "@", not "def"!
    pass
```

### The Solution: Understanding Structure

What if the computer could "read" code the way humans do - understanding that "def" means "function", that things inside parentheses are "parameters", etc.?

That's exactly what **parsers** do!

---

## 4. Understanding Tree-sitter (The Secret Weapon)

### What is Tree-sitter?

**Tree-sitter** is a tool that reads code and builds a **tree structure** from it - like an outline or a family tree, but for code.

Think of it like this:
- **Without Tree-sitter:** Reading a book by looking at each letter
- **With Tree-sitter:** Reading a book with chapter headings, section titles, and bullet points

### The Tree Structure (AST)

AST = **Abstract Syntax Tree**

"Abstract" = simplified, focused on structure  
"Syntax" = the grammar/rules of the language  
"Tree" = branching structure like a family tree

#### Example: From Code to Tree

**Python Code:**
```python
def calculate_sum(a, b):
    result = a + b
    return result
```

**What Tree-sitter Creates:**

```
function_definition (the whole function)
│
├── "def" (the keyword)
│
├── name: "calculate_sum" (the function's name)
│
├── parameters: (the inputs in parentheses)
│   ├── "a"
│   └── "b"
│
└── body: (everything inside the function)
    ├── assignment_statement (result = a + b)
    │   ├── target: "result"
    │   └── value: "a + b"
    │
    └── return_statement (return result)
        └── value: "result"
```

### How Tree-sitter Works (Step by Step)

```python
# ============================================================
# USING TREE-SITTER TO PARSE CODE
# ============================================================

# Line 1: Import tree-sitter's Python language support
# This gives us a parser that understands Python rules
from tree_sitter_languages import get_parser, get_language

# Line 2: Create a parser for Python
# Think of this as hiring a Python expert who will read the code
parser = get_parser("python")

# Line 3: Get the Python language definition
# This is like giving the expert a Python grammar book
language = get_language("python")

# Line 4: Define the Python code we want to parse
# This is the code the expert will analyze
code = """
def calculate_sum(a, b):
    result = a + b
    return result
"""

# Line 5: Parse the code into a tree structure
# .encode() converts the string to bytes (what the parser needs)
# parse() reads the code and builds the tree
tree = parser.parse(code.encode("utf-8"))

# Line 6: Get the root of the tree
# This is the starting point of our structure
root = tree.root_node

# Line 7: Print information about the root
# type = what kind of code element this is
# start_point = where it begins (line, column)
# end_point = where it ends (line, column)
print(f"Root type: {root.type}")           # Output: "module"
print(f"Starts at: {root.start_point}")    # Output: (0, 0)
print(f"Ends at: {root.end_point}")        # Output: (3, 0)
```

**What's happening in the parse step?**

```
Code String: "def calculate_sum(a, b):\n    result = a + b\n    return result"
                    ↓
            [Tree-sitter Parser reads character by character]
                    ↓
                    ↓  Recognizes "def" → this is a function!
                    ↓  Recognizes "calculate_sum" → this is the name!
                    ↓  Recognizes "(a, b)" → these are parameters!
                    ↓
Tree Structure:  function_definition
                 ├── name: identifier ("calculate_sum")
                 ├── parameters: ("a", "b")
                 └── body: ...
```

### Finding Things with Tree-sitter

Now comes the cool part - we can search this tree very precisely!

```python
# ============================================================
# FINDING ALL FUNCTIONS WITH TREE-SITTER
# ============================================================

# Line 1: Import the parser (same as before)
from tree_sitter_languages import get_parser, get_language

# Line 2: Create the parser
parser = get_parser("python")
language = get_language("python")

# Line 3: Define a query (like a search pattern)
# This query says: "Find all function definitions"
# (function_definition) means "look for nodes of type function_definition"
query = language.query("""
(function_definition)
""")

# Line 4: Parse some code
code = """
def hello():
    pass

class MyClass:
    def method(self):
        pass

def world():
    pass
"""
tree = parser.parse(code.encode("utf-8"))

# Line 5: Run the query on the parsed tree
# captures() returns all matching nodes
matches = query.captures(tree.root_node)

# Line 6: Print information about each function found
# Each match is a tuple: (node, capture_name)
for node, _ in matches:
    # node.type tells us what kind of code element this is
    # node.start_point tells us where it starts (line, column)
    print(f"Found a {node.type} at line {node.start_point[0] + 1}")

# Output:
# Found a function_definition at line 1
# Found a function_definition at line 4
# Found a function_definition at line 7
```

**Notice:** It found ALL functions, including the one inside the class (method), and didn't get confused by comments or anything else!

### Advanced: Finding Specific Things

Let's find functions with a specific name:

```python
# ============================================================
# FINDING A FUNCTION BY NAME
# ============================================================

# Line 1-2: Same setup as before
from tree_sitter_languages import get_parser, get_language
parser = get_parser("python")
language = get_language("python")

# Line 3: A more specific query
# This says: "Find function definitions where the name is 'calculate'"
# @func_name is a "capture" - we want to remember this part
# (#eq? @func_name "calculate") means "check if @func_name equals 'calculate'"
query = language.query("""
(function_definition
  name: (identifier) @func_name
  (#eq? @func_name "calculate"))
""")

# Line 4: Parse code with multiple functions
code = """
def helper():
    pass

def calculate(x, y):
    return x + y

def another_helper():
    pass
"""
tree = parser.parse(code.encode("utf-8"))

# Line 5: Run the query
matches = query.captures(tree.root_node)

# Line 6: Print results
for node, capture_name in matches:
    # node.text gives us the actual text from the code
    # decode converts bytes back to a string
    func_name = node.text.decode("utf-8")
    print(f"Found function named: {func_name}")
    print(f"At line: {node.start_point[0] + 1}")

# Output:
# Found function named: calculate
# At line: 4
```

### How Tree-sitter is Used in SWE-agent

Now you understand the magic! Here's how SWE-agent actually uses tree-sitter:

```python
# ============================================================
# HOW SWE-AGENT'S "filemap" TOOL WORKS
# ============================================================

# This tool shows a file outline - like a table of contents

from tree_sitter_languages import get_language, get_parser

# Step 1: Create parser
parser = get_parser("python")
language = get_language("python")

# Step 2: Read a file
with open("big_file.py", "r") as f:
    code = f.read()

# Step 3: Parse it
tree = parser.parse(code.encode("utf-8"))

# Step 4: Query to find all function bodies
# This finds everything inside a function (the body)
query = language.query("""
(function_definition
  body: (_) @body)
""")

# Step 5: Get all the function bodies
matches = query.captures(tree.root_node)

# Step 6: For each function body that's long, show "..." instead
for node, _ in matches:
    start_line = node.start_point[0]  # Line where body starts
    end_line = node.end_point[0]      # Line where body ends
    
    # If function is longer than 5 lines, hide the details
    if end_line - start_line >= 5:
        print(f"Lines {start_line+1}-{end_line+1}: [function body hidden]")
    else:
        # Show short functions completely
        print(code.split('\n')[start_line:end_line+1])

# Result: You see the file structure without drowning in code!
```

---

## 5. Why This Matters: Real Examples

### Scenario 1: Finding a Bug

**The Problem:** A bug report says "The `process_data` function crashes"

**Without Tree-sitter (Text Search):**
```
Agent: search_dir "process_data" .
Computer: Found 50 matches!
  - Line 10: def process_data(raw):
  - Line 25: result = process_data(data)
  - Line 47: # TODO: refactor process_data
  - Line 89: print("calling process_data")
  - ... 46 more matches
Agent: Ugh, which one is the actual function definition?
```

**With Tree-sitter (Structure Search):**
```
Agent: find_definition process_data
Computer: Found 1 function definition:
  - File: utils.py, Line 10
  - Name: process_data
  - Parameters: (raw)
  - Body: 15 lines
Agent: Perfect! Now I can view just that function.
```

### Scenario 2: Understanding Code Impact

**The Problem:** You want to change a function, but need to know what else will break.

**Without Tree-sitter:**
```
Agent: search_dir "calculate_tax" .
Computer: Found in 12 files, 47 occurrences
Agent: Which ones are calls vs definitions vs comments?
```

**With Tree-sitter:**
```
Agent: find_references calculate_tax
Computer: Found 8 actual function calls:
  - checkout.py line 15
  - invoice.py line 42
  - report.py lines 10, 35
  ...
Computer: 1 function definition: taxes.py line 8
Computer: 3 comments mentioning it (safe to ignore)
```

### Scenario 3: The Filemap Tool in Action

**The Problem:** A file is 500 lines long. You want to understand its structure quickly.

**Regular View (overwhelming):**
```python
def function_one():
    x = 1
    y = 2
    z = 3
    # ... 20 more lines

def function_two():
    a = 1
    b = 2
    # ... 30 more lines

# ... repeat 10 more times
```

**Filemap View (with Tree-sitter):**
```
     1 def function_one(): ... eliding lines 2-22 ...
    23 def function_two(): ... eliding lines 24-55 ...
    56 def function_three():
    57     return 42
    58 class MyClass: ... eliding lines 59-200 ...
   201 def main(): ... eliding lines 202-500 ...
```

**You instantly see:** There are 4 functions, 1 class, and `main` is at the bottom!

---

## 6. Summary: What We Learned

### Key Concepts

| Concept | Simple Explanation | Analogy |
|---------|-------------------|---------|
| **Tool** | A command the agent can use | A special power in a video game |
| **Parser** | Code that reads and understands other code | A translator |
| **Parser Generator** | A tool that writes parsers automatically | A robot that writes translator robots |
| **Tree-sitter** | A parser generator that builds trees from code | An X-ray machine for code |
| **AST** | A structured representation of code | An outline or family tree for code |
| **Query** | A pattern to search the AST | A "Find" function that understands structure |

### The Big Picture

```
┌─────────────────────────────────────────────────────────────────┐
│                    HOW IT ALL FITS TOGETHER                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1. AGENT WANTS TO UNDERSTAND CODE                              │
│           │                                                     │
│           ▼                                                     │
│  2. CODE IS JUST TEXT (like "def foo(): pass")                  │
│           │                                                     │
│           ▼                                                     │
│  3. TREE-SITTER PARSES IT (converts text to structure)          │
│           │                                                     │
│           ▼                                                     │
│  4. AGENT QUERIES THE TREE (asks precise questions)             │
│           │                                                     │
│           ▼                                                     │
│  5. AGENT GETS ACCURATE ANSWERS (not just text matches)         │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Without vs With Tree-sitter

| Task | Without Tree-sitter | With Tree-sitter |
|------|---------------------|------------------|
| Find all functions | Regex search (70% accurate) | Structure query (99% accurate) |
| Find function by name | Search all occurrences, guess which is definition | Direct lookup of definition node |
| Understand scope | Impossible | Tree shows nesting clearly |
| Handle edge cases | Misses decorators, async, etc. | Handles all Python syntax |

### Why This Helps SWE-agent

1. **Faster:** Structure queries are faster than scanning all text
2. **Accurate:** No false positives from comments or strings
3. **Smarter:** Understands Python syntax deeply
4. **Extensible:** Works for 50+ programming languages

---

## Practice Exercise

Try to predict what this code would output:

```python
from tree_sitter_languages import get_parser, get_language

parser = get_parser("python")
language = get_language("python")

code = """
def greet(name):
    print(f"Hello, {name}!")

def farewell(name):
    print(f"Goodbye, {name}!")
"""

tree = parser.parse(code.encode("utf-8"))

query = language.query("""
(function_definition
  name: (identifier) @func_name)
""")

matches = query.captures(tree.root_node)
for node, _ in matches:
    print(node.text.decode("utf-8"))
```

<details>
<summary>Click to see answer</summary>

```
greet
farewell
```

The query finds all function definitions and captures their names!
</details>

---

## Next Steps

Now that you understand:
- How tools work in SWE-agent
- How code is stored as text
- How tree-sitter converts text to structure
- Why structured queries are better than text search

You're ready to understand more advanced topics:
- How to write custom tools for SWE-agent
- How to build code intelligence tools using tree-sitter
- How SWE-agent decides which tools to use

**Recommended reading:**
1. Look at the existing tools in the `tools/` directory
2. Try modifying a simple tool
3. Experiment with tree-sitter queries

---

*Happy coding!* 🌳
