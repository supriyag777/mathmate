import os
import re
import math
from PIL import Image
import pytesseract

from django.shortcuts import render
from sympy import symbols, solve
from sympy.parsing.sympy_parser import (
    parse_expr, standard_transformations, implicit_multiplication_application
)

from .models import MathQuery

# Set Tesseract binary path conditionally for local Windows environments
if os.name == 'nt':
    pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"


def home(request):
    problem = ""
    formula = ""
    solution = ""
    answer = None
    error = None

    if request.method == "POST":
        # Extract inputs from either image upload or text field
        image = request.FILES.get("question_image")
        text_input = request.POST.get("problem", "").strip()

        if image:
            try:
                img = Image.open(image)
                extracted_text = pytesseract.image_to_string(img).strip()

                if extracted_text:
                    math_lines = [
                        line for line in extracted_text.splitlines()
                        if re.search(r'\d', line) and re.search(r'[\+\-\*/=x×÷()]', line)
                    ]
                    cleaned = math_lines[-1] if math_lines else extracted_text
                    cleaned = cleaned.replace('×', '*').replace('÷', '/')
                    cleaned = cleaned.rstrip('=').strip()
                    problem = cleaned
                else:
                    error = "Couldn't read the question image."
            except Exception as e:
                error = f"Error processing image: {str(e)}"
        elif text_input:
            problem = text_input

        lower_problem = problem.lower()

        if not problem and not error:
            error = "Please enter a question or upload an image."

        # --- MATH PROCESSING LOGIC ---
        if error:
            pass

        # Percentage problem (Direct numeric match)
        elif percentage_match := re.match(r"(\d+(?:\.\d+)?)\s*%\s*of\s*(\d+(?:\.\d+)?)", lower_problem):
            percentage = float(percentage_match.group(1))
            number = float(percentage_match.group(2))
            result = (percentage * number) / 100
            formula = "Percentage × Number / 100"
            solution = f"{percentage} × {number} / 100"
            answer = result

        # Natural Language Percentage
        elif "%" in problem and ("of" in lower_problem or "what" in lower_problem):
            numbers = re.findall(r"\d+(?:\.\d+)?", problem)
            if len(numbers) >= 2:
                percentage = float(numbers[0])
                number = float(numbers[1])
                result = (percentage / 100) * number
                formula = "Percentage = (Percentage / 100) × Number"
                solution = (
                    f"{percentage:g}% of {number:g}<br>"
                    f"= ({percentage:g} / 100) × {number:g}<br>"
                    f"= {result:g}"
                )
                answer = f"{percentage:g}% of {number:g} = {result:g}"
            else:
                error = "Please enter a valid percentage question."

        # Average
        elif "average" in lower_problem and "missing" not in lower_problem:
            numbers = [float(n) for n in re.findall(r"\d+(?:\.\d+)?", problem)]
            if numbers:
                total = sum(numbers)
                average = total / len(numbers)
                formula = "Average = Sum of values / Number of values"
                solution = (
                    f"Values = {', '.join(f'{n:g}' for n in numbers)}<br>"
                    f"Sum = {total:g}<br>"
                    f"Count = {len(numbers)}<br>"
                    f"Average = {total:g} / {len(numbers)}<br>"
                    f"= {average:g}"
                )
                answer = f"Average = {average:g}"
            else:
                error = "Please provide numbers to calculate the average."

        # Ratio and Proportion
        elif "ratio" in lower_problem and "age" not in lower_problem:
            ratio_match = re.search(r"(\d+(?:\.\d+)?)\s*:\s*(\d+(?:\.\d+)?)", problem)
            numbers = re.findall(r"\d+(?:\.\d+)?", problem)
            if ratio_match and len(numbers) >= 3:
                first = float(ratio_match.group(1))
                second = float(ratio_match.group(2))
                total = float(numbers[-1])
                total_parts = first + second
                first_value = (first / total_parts) * total
                second_value = (second / total_parts) * total
                formula = "Value = (Ratio part / Total ratio parts) × Total"
                solution = (
                    f"Total parts = {first} + {second} = {total_parts}<br>"
                    f"First value = ({first}/{total_parts}) × {total} = {first_value}<br>"
                    f"Second value = ({second}/{total_parts}) × {total} = {second_value}"
                )
                answer = f"Values = {first_value} and {second_value}"
            elif ratio_match:
                first = ratio_match.group(1)
                second = ratio_match.group(2)
                formula = "Ratio = First quantity : Second quantity"
                solution = f"{first} : {second}"
                answer = f"{first}:{second}"
            else:
                error = "Please enter a ratio like 2:3."

        # Simple Interest
        elif "si" in lower_problem or "simple interest" in lower_problem:
            numbers = re.findall(r"\d+(?:\.\d+)?", problem)
            if "find principal" in lower_problem and len(numbers) >= 3:
                si, rate, time = map(float, numbers[:3])
                principal = (si * 100) / (rate * time)
                formula = "P = (SI × 100) / (R × T)"
                solution = f"SI = {si:g}<br>Rate = {rate:g}%<br>Time = {time:g}<br>Principal = {principal:.2f}"
                answer = f"Principal = {principal:.2f}"
            elif "find rate" in lower_problem and len(numbers) >= 3:
                si, principal, time = map(float, numbers[:3])
                rate = (si * 100) / (principal * time)
                formula = "R = (SI × 100) / (P × T)"
                solution = f"SI = {si:g}<br>Principal = {principal:g}<br>Time = {time:g}<br>Rate = {rate:.2f}%"
                answer = f"Rate = {rate:.2f}%"
            elif len(numbers) >= 3:
                principal, rate, time = map(float, numbers[:3])
                interest = (principal * rate * time) / 100
                formula = "SI = (P × R × T) / 100"
                solution = f"({principal} × {rate} × {time}) / 100"
                answer = f"Simple Interest = {interest}"
            else:
                error = "Please enter Principal, Rate and Time."

        # Compound Interest
        elif "ci" in lower_problem or "compound interest" in lower_problem:
            numbers = re.findall(r"\d+(?:\.\d+)?", problem)
            if len(numbers) >= 3:
                principal, rate, time = map(float, numbers[:3])
                amount = principal * (1 + rate / 100) ** time
                interest = amount - principal
                formula = "CI = P(1 + R/100)^T - P"
                solution = f"{principal} × (1 + {rate}/100)^{time} - {principal}"
                answer = f"Compound Interest = {interest:.2f}"
            else:
                error = "Please enter Principal, Rate and Time."

        # Time and Work
        elif "work" in lower_problem and "time" in lower_problem:
            numbers = re.findall(r"\d+(?:\.\d+)?", problem)
            if len(numbers) >= 2:
                time1, time2 = float(numbers[0]), float(numbers[1])
                work_rate = (1 / time1) + (1 / time2)
                total_time = 1 / work_rate
                formula = "Combined Work Rate = 1/T1 + 1/T2"
                solution = (
                    f"1/{time1} + 1/{time2} = {work_rate:.4f} <br />"
                    f"Time = 1/{work_rate:.4f} = {total_time:.2f} days"
                )
                answer = f"Together they complete the work in {total_time:.2f} days"
            else:
                error = "Please enter the time taken by both persons."

        # Speed, Distance and Time
        elif "speed" in lower_problem or "distance" in lower_problem or "time" in lower_problem:
            numbers = re.findall(r"\d+(?:\.\d+)?", problem)
            if len(numbers) >= 2:
                first, second = float(numbers[0]), float(numbers[1])
                if "speed" in lower_problem and "time" in lower_problem:
                    distance = first * second
                    formula = "Distance = Speed × Time"
                    solution = f"{first} × {second} = {distance}"
                    answer = f"Distance = {distance}"
                elif "distance" in lower_problem and "time" in lower_problem:
                    speed = first / second
                    formula = "Speed = Distance / Time"
                    solution = f"{first} / {second} = {speed}"
                    answer = f"Speed = {speed}"
                elif "distance" in lower_problem and "speed" in lower_problem:
                    time = first / second
                    formula = "Time = Distance / Speed"
                    solution = f"{first} / {second} = {time}"
                    answer = f"Time = {time}"
                else:
                    error = "Please specify Speed, Distance or Time."
            else:
                error = "Please enter two values."

        # Age Problems
        elif "age" in lower_problem:
            ratios = re.findall(r"(\d+)\s*:\s*(\d+)", problem)
            years_match = re.search(r"after\s+(\d+)\s*years?", lower_problem)
            numbers = re.findall(r"\d+(?:\.\d+)?", problem)

            if len(ratios) >= 2 and years_match:
                r1, r2 = map(float, ratios[0])
                r3, r4 = map(float, ratios[1])
                years = float(years_match.group(1))
                x = (years * (r4 - r3)) / (r3 * r2 - r4 * r1)
                age1, age2 = r1 * x, r2 * x
                formula = "Present ages = First ratio × x and Second ratio × x"
                solution = (
                    f"Let present ages be {r1:g}x and {r2:g}x<br>"
                    f"After {years:g} years: ({r1:g}x + {years:g}) / ({r2:g}x + {years:g}) = {r3:g}/{r4:g}<br>"
                    f"x = {x:g}<br>A's present age = {age1:g}<br>B's present age = {age2:g}"
                )
                answer = f"A = {age1:g} years, B = {age2:g} years"
            elif ratios and len(numbers) >= 3:
                first, second = map(float, ratios[0])
                total_age = float(numbers[-1])
                total_parts = first + second
                age1 = (first / total_parts) * total_age
                age2 = (second / total_parts) * total_age
                formula = "Age = (Ratio part / Total ratio parts) × Total age"
                solution = (
                    f"Total parts = {first:g} + {second:g} = {total_parts:g}<br>"
                    f"A's age = ({first:g}/{total_parts:g}) × {total_age:g} = {age1:g}<br>"
                    f"B's age = ({second:g}/{total_parts:g}) × {total_age:g} = {age2:g}"
                )
                answer = f"A = {age1:g} years, B = {age2:g} years"
            else:
                error = "Please provide valid age parameters."

        # HCF and LCM
        elif "hcf" in lower_problem or "lcm" in lower_problem:
            numbers = [int(n) for n in re.findall(r"\d+", problem)]
            if len(numbers) >= 2:
                hcf_value = numbers[0]
                lcm_value = numbers[0]
                for num in numbers[1:]:
                    hcf_value = math.gcd(hcf_value, num)
                    lcm_value = math.lcm(lcm_value, num)
                formula = "HCF = Highest Common Factor<br>LCM = Least Common Multiple"
                solution = f"Numbers = {', '.join(map(str, numbers))}<br>HCF = {hcf_value}<br>LCM = {lcm_value}"
                if "hcf" in lower_problem and "lcm" not in lower_problem:
                    answer = f"HCF = {hcf_value}"
                elif "lcm" in lower_problem and "hcf" not in lower_problem:
                    answer = f"LCM = {lcm_value}"
                else:
                    answer = f"HCF = {hcf_value}, LCM = {lcm_value}"
            else:
                error = "Please enter at least two numbers."

        # Quadratic Equations
        elif "x^2" in lower_problem or "x²" in lower_problem or "quadratic" in lower_problem:
            try:
                equation = problem.lower().replace("quadratic", "").strip()
                clean_eq = equation.replace("x²", "x**2").replace("^2", "**2")
                if "=" in clean_eq:
                    left, right = clean_eq.split("=")
                    expr = parse_expr(left) - parse_expr(right)
                else:
                    expr = parse_expr(clean_eq)
                x = symbols('x')
                solutions = solve(expr, x)
                formula = "Quadratic Formula: ax² + bx + c = 0"
                solution = f"Roots found: {solutions}"
                answer = f"x = {solutions}"
            except Exception:
                error = "Could not solve the quadratic equation."

        # Circle Area/Perimeter
        elif "circle" in lower_problem and ("area" in lower_problem or "perimeter" in lower_problem or "circumference" in lower_problem):
            numbers = re.findall(r"\d+(?:\.\d+)?", problem)
            if numbers:
                r = float(numbers[0])
                area = math.pi * (r ** 2)
                circumference = 2 * math.pi * r
                formula = "Area = πr², Circumference = 2πr"
                solution = f"Radius = {r}<br>Area = {area:.2f}<br>Circumference = {circumference:.2f}"
                answer = f"Area = {area:.2f}, Circumference = {circumference:.2f}"
            else:
                error = "Please provide the radius of the circle."

        # Basic Math Fallback
        else:
            try:
                transformations = standard_transformations + (implicit_multiplication_application,)
                result = parse_expr(problem, transformations=transformations)
                if result.free_symbols:
                    answer = str(result)
                else:
                    evaluated = result.evalf()
                    answer = int(evaluated) if evaluated == int(evaluated) else round(float(evaluated), 4)
                formula = "Direct Calculation"
                solution = f"{problem} = {answer}"
            except Exception:
                error = "Sorry, I couldn't solve that problem."

        # Save to database upon successful calculation
        if answer is not None and not error:
            MathQuery.objects.create(
                problem=problem,
                formula=formula,
                solution=solution,
                answer=str(answer)
            )

    # Fetch last 5 queries to display history
    history = MathQuery.objects.order_by('-created_at')[:5]

    return render(
        request,
        "solver/home.html",
        {
            "answer": answer,
            "formula": formula,
            "solution": solution,
            "error": error,
            "problem": problem,
            "history": history,
        }
    )