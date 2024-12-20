import csv
from collections import Counter
import random

def get_integer_input(prompt):
    while True:
        try:
            return int(input(prompt))
        except ValueError:
            print("Invalid input, please enter an integer.")

def get_unique_numbers(prompt, count, allow_duplicates=False):
    numbers = []
    for i in range(count):
        while True:
            num = get_integer_input(f"{prompt} {i+1}: ")
            if not allow_duplicates and num in numbers:
                print("You have already entered this number, please enter a different one.")
            else:
                numbers.append(num)
                break
    return numbers

def load_historical_data(filename, main_count, supp_count=0):
    """
    Load historical data from the specified CSV file.
    Assumes:
    col1: draw number
    col2: draw date
    Following columns: main numbers first, then supplementary/powerball numbers.
    """
    main_numbers = []
    supp_numbers = []
    
    try:
        with open(filename, 'r', newline='', encoding='utf-8') as f:
            reader = csv.reader(f)
            header = next(reader)  # skip header if present
            for row in reader:
                # We expect at least 2 + main_count (+ supp_count) columns
                if len(row) < (2 + main_count + supp_count):
                    continue
                
                row_main = row[2:2+main_count]
                row_main = [int(n) for n in row_main if n.isdigit()]
                if len(row_main) != main_count:
                    continue
                main_numbers.extend(row_main)
                
                if supp_count > 0:
                    row_supp = row[2+main_count:2+main_count+supp_count]
                    row_supp = [int(n) for n in row_supp if n.isdigit()]
                    if len(row_supp) == supp_count:
                        supp_numbers.extend(row_supp)
                        
    except FileNotFoundError:
        print(f"File {filename} not found.")
    except Exception as e:
        print(f"An error occurred while reading {filename}: {e}")
                    
    return main_numbers, supp_numbers

def weighted_sample_without_replacement(population, weights, k):
    """
    Select k unique elements from population based on the provided weights.
    Higher weight increases the probability of being selected.
    """
    selected = []
    population = population.copy()
    weights = weights.copy()

    for _ in range(k):
        if not population:
            break
        total = sum(weights)
        if total == 0:
            # If all remaining weights are zero, select uniformly
            selected.append(population.pop(0))
            weights.pop(0)
            continue
        r = random.uniform(0, total)
        upto = 0
        for i, w in enumerate(weights):
            upto += w
            if upto >= r:
                selected.append(population.pop(i))
                weights.pop(i)
                break
    return selected

def generate_lines(main_count, supp_count, pool_main, pool_supp, lines_to_generate=5, main_weights=None, supp_weights=None, deterministic=False):
    """
    Generate lottery lines based on historical frequency.
    
    Parameters:
    - main_count: Number of main numbers per line.
    - supp_count: Number of supplementary numbers per line.
    - pool_main: List of main numbers sorted by frequency (descending).
    - pool_supp: List of supplementary numbers sorted by frequency (descending).
    - lines_to_generate: Number of lines to generate.
    - main_weights: Corresponding weights for main numbers (used in weighted sampling).
    - supp_weights: Corresponding weights for supplementary numbers (used in weighted sampling).
    - deterministic: If True, select distinct top frequency numbers for each line.
                     If False, use weighted random sampling.
    
    Returns:
    - List of tuples containing (main_numbers, supp_numbers) for each line.
    """
    generated_lines = []
    
    if deterministic:
        # Calculate the total number of available main and supplementary numbers
        total_main_available = len(pool_main)
        total_supp_available = len(pool_supp)
        
        # Check if there are enough numbers to generate the desired number of lines without repetition
        if total_main_available < main_count * lines_to_generate:
            print(f"Not enough main numbers to generate {lines_to_generate} lines without repetition.")
            print(f"Available main numbers: {total_main_available}, Required: {main_count * lines_to_generate}")
            return generated_lines
        
        if supp_count > 0 and len(pool_supp) < supp_count * lines_to_generate:
            print(f"Not enough supplementary numbers to generate {lines_to_generate} lines without repetition.")
            print(f"Available supplementary numbers: {len(pool_supp)}, Required: {supp_count * lines_to_generate}")
            return generated_lines
        
        for i in range(lines_to_generate):
            # Calculate start and end indices for slicing
            start_main = i * main_count
            end_main = start_main + main_count
            chosen_main = sorted(pool_main[start_main:end_main])
            
            if supp_count > 0:
                start_supp = i * supp_count
                end_supp = start_supp + supp_count
                chosen_supp = sorted(pool_supp[start_supp:end_supp])
            else:
                chosen_supp = []
            
            generated_lines.append((chosen_main, chosen_supp))
    else:
        for _ in range(lines_to_generate):
            # Weighted sampling without replacement for main numbers
            chosen_main = weighted_sample_without_replacement(pool_main, main_weights, main_count)
            chosen_main = sorted(chosen_main)
            
            if supp_count > 0:
                chosen_supp = weighted_sample_without_replacement(pool_supp, supp_weights, supp_count)
                chosen_supp = sorted(chosen_supp)
            else:
                chosen_supp = []
            generated_lines.append((chosen_main, chosen_supp))
    
    return generated_lines

def check_ticket_mode(games):
    # Ask which game
    print("Choose a game:")
    for key, g in games.items():
        print(f"{key}. {g['name']}")
    choice = input("Enter the number of the game: ").strip()
    
    if choice not in games:
        print("Invalid choice.")
        return
    game = games[choice]
    main_count = game["main_count"]
    supp_count = game.get("supp_count", 0)
    powerball_count = game.get("powerball_count", 0)
    
    # Ask how many lines the user has
    lines_count = get_integer_input("How many lines do you have on your ticket? ")
    if lines_count <= 0:
        print("Number of lines must be greater than 0.")
        return

    user_lines = []
    print("\nEnter your lines:")
    for i in range(lines_count):
        print(f"Line {i+1}:")
        user_main = get_unique_numbers("Main number", main_count)
        user_supp = []
        user_powerball = []

        if supp_count > 0:
            user_supp = get_unique_numbers("Supplementary number", supp_count)
        elif powerball_count > 0:
            user_powerball = get_unique_numbers("Powerball number", powerball_count)

        user_lines.append({
            "main": user_main,
            "supp": user_supp,
            "powerball": user_powerball
        })

    # Now ask for the winning numbers
    print("\nEnter the winning numbers:")
    winning_main = get_unique_numbers("Winning main number", main_count)

    winning_supp = []
    winning_powerball = []
    if supp_count > 0:
        winning_supp = get_unique_numbers("Winning supplementary number", supp_count)
    elif powerball_count > 0:
        winning_powerball = get_unique_numbers("Winning powerball number", powerball_count)

    # Check each user line
    print("\nResults:")
    for i, line in enumerate(user_lines, start=1):
        main_matches = len(set(line["main"]).intersection(winning_main))
        supp_matches = 0
        powerball_match = 0

        if supp_count > 0:
            supp_matches = len(set(line["supp"]).intersection(winning_supp))
            print(f"Line {i}: {main_matches} main matches, {supp_matches} supplementary matches")
        elif powerball_count > 0:
            powerball_match = 1 if line["powerball"][0] in winning_powerball else 0
            print(f"Line {i}: {main_matches} main matches, Powerball match: {powerball_match}")
        else:
            print(f"Line {i}: {main_matches} main matches")

def upcoming_game_mode(games):
    # User wants to generate lines based on historical frequency
    print("Choose a game for upcoming draw:")
    for key, g in games.items():
        print(f"{key}. {g['name']}")
    choice = input("Enter the number of the game: ").strip()
    
    if choice not in games:
        print("Invalid choice.")
        return
    
    game = games[choice]
    main_count = game["main_count"]
    supp_count = game.get("supp_count", 0)
    powerball_count = game.get("powerball_count", 0)
    
    # If powerball_count is defined, treat it as supp_count for loading data
    total_supp = supp_count if supp_count > 0 else (powerball_count if powerball_count > 0 else 0)
    
    main_numbers, supp_numbers = load_historical_data(game["file"], main_count, total_supp)
    if not main_numbers:
        print("No main numbers loaded. Check CSV formatting.")
        return
    
    main_frequency = Counter(main_numbers)
    main_sorted = [num for num, freq in main_frequency.most_common()]
    main_weights = [main_frequency[num] for num in main_sorted]
    
    supp_sorted = []
    supp_weights = []
    if total_supp > 0 and supp_numbers:
        supp_frequency = Counter(supp_numbers)
        supp_sorted = [num for num, freq in supp_frequency.most_common()]
        supp_weights = [supp_frequency[num] for num in supp_sorted]
    
    pool_main = main_sorted
    pool_supp = supp_sorted
    
    lines_to_generate = get_integer_input("How many lines would you like to generate based on historical frequency? ")
    if lines_to_generate <= 0:
        print("Number of lines must be greater than 0.")
        return

    # Check if deterministic mode is feasible
    if lines_to_generate > 0:
        max_main_lines = len(pool_main) // main_count
        max_supp_lines = len(pool_supp) // supp_count if supp_count > 0 else float('inf')
        max_possible_lines = min(max_main_lines, max_supp_lines)
    else:
        max_possible_lines = 0

    # Ask the user whether to use deterministic selection or weighted random sampling
    while True:
        deterministic_input = input("Do you want to use deterministic selection (select top frequency numbers without repetition)? (y/n): ").strip().lower()
        if deterministic_input in ['y', 'n']:
            deterministic = deterministic_input == 'y'
            break
        else:
            print("Please enter 'y' or 'n'.")

    if deterministic and lines_to_generate > max_possible_lines:
        print(f"Cannot generate {lines_to_generate} lines without repeating numbers.")
        print(f"Maximum lines that can be generated without repetition: {max_possible_lines}")
        return

    lines = generate_lines(
        main_count, 
        total_supp, 
        pool_main, 
        pool_supp, 
        lines_to_generate, 
        main_weights, 
        supp_weights,
        deterministic=deterministic
    )
    
    if lines:
        print(f"\nGenerated {lines_to_generate} lines for {game['name']} based on frequency:")
        for idx, (m, s) in enumerate(lines, start=1):
            if total_supp > 0:
                print(f"Line {idx}: Main - {m}, Supp - {s}")
            else:
                print(f"Line {idx}: Main - {m}")
    else:
        print("No lines were generated due to insufficient data.")

def frequency_view_mode(games):
    # User wants to view frequency of each number
    print("Choose a game to view frequency:")
    for key, g in games.items():
        print(f"{key}. {g['name']}")
    choice = input("Enter the number of the game: ").strip()
    
    if choice not in games:
        print("Invalid choice.")
        return
    
    game = games[choice]
    main_count = game["main_count"]
    supp_count = game.get("supp_count", 0)
    powerball_count = game.get("powerball_count", 0)
    total_supp = supp_count if supp_count > 0 else (powerball_count if powerball_count > 0 else 0)
    
    main_numbers, supp_numbers = load_historical_data(game["file"], main_count, total_supp)
    if not main_numbers:
        print("No data loaded. Check CSV formatting.")
        return
    
    main_frequency = Counter(main_numbers)
    # The number of draws can be inferred from how many main numbers total we have.
    # Each draw has `main_count` main numbers.
    num_draws = len(main_numbers) // main_count
    print(f"\nFrequency of main numbers for {game['name']}:")
    for num, freq in main_frequency.most_common():
        percentage = (freq / num_draws) * 100
        print(f"Number {num}: drawn in {freq}/{num_draws} draws = {percentage:.2f}%")
    
    if total_supp > 0 and supp_numbers:
        supp_frequency = Counter(supp_numbers)
        # Similarly, number of draws for supp numbers:
        # each draw has `supp_count` or `powerball_count` supp/powerball numbers
        num_draws_supp = len(supp_numbers) // total_supp
        print(f"\nFrequency of supplementary/powerball numbers for {game['name']}:")
        for num, freq in supp_frequency.most_common():
            percentage = (freq / num_draws_supp) * 100
            print(f"Number {num}: drawn in {freq}/{num_draws_supp} draws = {percentage:.2f}%")

def main():
    # Define games and their configurations
    games = {
        "1": {
            "name": "Saturday Lotto",
            "file": "saturday-lotto.csv",
            "main_count": 6,
            "supp_count": 2
        },
        "2": {
            "name": "Oz Lotto",
            "file": "oz-lotto.csv",
            "main_count": 7,
            "supp_count": 2
        },
        "3": {
            "name": "Powerball",
            "file": "powerball.csv",
            "main_count": 7,
            "powerball_count": 1
        },
        "4": {
            "name": "Set for Life",
            "file": "set-for-life.csv",
            "main_count": 7,
            "supp_count": 0
        }
    }
    
    while True:
        print("\nDo you want to:")
        print("1. Check your ticket against winning numbers")
        print("2. Generate numbers for an upcoming game based on historical frequency")
        print("3. View frequency of each number for a chosen game")
        print("4. Exit")
        mode = input("Enter 1, 2, 3 or 4: ").strip()
        
        if mode == "1":
            check_ticket_mode(games)
        elif mode == "2":
            upcoming_game_mode(games)
        elif mode == "3":
            frequency_view_mode(games)
        elif mode == "4":
            print("Goodbye!")
            break
        else:
            print("Invalid choice.")

if __name__ == "__main__":
    main()

