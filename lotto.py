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
      Following columns: main numbers first, then supplementary numbers.
    """
    main_numbers = []
    supp_numbers = []
    
    try:
        with open(filename, 'r', newline='', encoding='utf-8') as f:
            reader = csv.reader(f)
            header = next(reader, None)  # Attempt to skip header if present
            for row in reader:
                # We expect at least 2 + main_count (+ supp_count) columns
                if len(row) < (2 + main_count + supp_count):
                    continue
                
                # Extract main numbers
                row_main = row[2:2+main_count]
                row_main = [int(n) for n in row_main if n.isdigit()]
                if len(row_main) != main_count:
                    continue
                main_numbers.extend(row_main)
                
                # Extract supplementary numbers
                if supp_count > 0:
                    row_supp = row[2+main_count : 2+main_count+supp_count]
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
    Select k unique elements from 'population' based on 'weights'.
    Higher weight => higher probability of being selected.
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

def generate_lines(main_count, supp_count, pool_main, pool_supp,
                   lines_to_generate=5, main_weights=None, supp_weights=None,
                   deterministic=False):
    """
    Generate lottery lines based on historical frequency.
    
    - main_count: Number of main numbers per line.
    - supp_count: Number of supplementary numbers per line.
    - pool_main: List of main numbers sorted by frequency (descending).
    - pool_supp: List of supplementary numbers sorted by frequency (descending).
    - lines_to_generate: How many lines to generate.
    - main_weights: Weights for main numbers (for weighted sampling).
    - supp_weights: Weights for supplementary numbers (for weighted sampling).
    - deterministic: If True, pick top frequency numbers without repetition.
    """
    generated_lines = []
    
    if deterministic:
        # Check total availability for a no-repetition scenario
        total_main_available = len(pool_main)
        total_supp_available = len(pool_supp)
        
        if total_main_available < main_count * lines_to_generate:
            print(f"Not enough main numbers to generate {lines_to_generate} lines without repetition.")
            print(f"Available main numbers: {total_main_available}, Required: {main_count * lines_to_generate}")
            return generated_lines
        
        if supp_count > 0 and total_supp_available < supp_count * lines_to_generate:
            print(f"Not enough supplementary numbers to generate {lines_to_generate} lines without repetition.")
            print(f"Available supplementary numbers: {total_supp_available}, Required: {supp_count * lines_to_generate}")
            return generated_lines
        
        for i in range(lines_to_generate):
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
            chosen_main = weighted_sample_without_replacement(pool_main, main_weights, main_count)
            chosen_main = sorted(chosen_main)
            
            if supp_count > 0:
                chosen_supp = weighted_sample_without_replacement(pool_supp, supp_weights, supp_count)
                chosen_supp = sorted(chosen_supp)
            else:
                chosen_supp = []
            
            generated_lines.append((chosen_main, chosen_supp))
    
    return generated_lines

def read_user_lines_from_csv(filename, game):
    """
    Reads ticket lines from a CSV file generated by this tool.
    Format:
      If user_supp_count > 0:
         "Line #", "Main Numbers" (space-separated), "Supplementary Numbers" (space-separated)
      If user_supp_count == 0:
         "Line #", "Main Numbers" (space-separated)
    """
    user_lines = []
    main_count = game["main_count"]
    supp_count = game["user_supp_count"]  # Number of supplementary numbers the user picks
    
    try:
        with open(filename, 'r', newline='', encoding='utf-8') as f:
            reader = csv.reader(f)
            
            # Try reading the first row as a potential header
            first_row = next(reader, None)
            if first_row and first_row[0].strip().lower() == "line #":
                # It's a header row, skip it
                pass
            else:
                # Possibly a real data row, so re-inject it
                if first_row is not None:
                    all_rows = [first_row] + list(reader)
                else:
                    all_rows = []
                reader = iter(all_rows)
            
            for row in reader:
                expected_cols = 3 if supp_count > 0 else 2
                if len(row) < expected_cols:
                    print(f"Skipping row (not enough columns): {row}")
                    continue
                
                main_str = row[1].strip()
                mains = main_str.split()
                
                # Check length
                if len(mains) != main_count:
                    print(f"Skipping row (main count mismatch): {row}")
                    continue
                
                # Convert to int
                try:
                    main_nums = [int(x) for x in mains]
                except ValueError:
                    print(f"Skipping row (could not convert main numbers to int): {row}")
                    continue
                
                supp_nums = []
                if supp_count > 0:
                    supp_str = row[2].strip()
                    sups = supp_str.split()
                    
                    if len(sups) != supp_count:
                        print(f"Skipping row (supp count mismatch): {row}")
                        continue
                    try:
                        supp_nums = [int(x) for x in sups]
                    except ValueError:
                        print(f"Skipping row (could not convert supplementary to int): {row}")
                        continue
                
                user_lines.append({
                    "main": main_nums,
                    "supp": supp_nums
                })
    
    except FileNotFoundError:
        print(f"File {filename} not found.")
    except Exception as e:
        print(f"An error occurred while reading {filename}: {e}")
    
    return user_lines

def check_ticket_mode(games):
    from collections import Counter
    
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
    user_supp_count = game["user_supp_count"]
    supp_count = game["supp_count"]  # Number of winning supplementary numbers
    
    # Let the user choose between reading ticket lines from CSV or manual input
    from_csv = input("Do you want to read your ticket lines from a CSV file? (y/n): ").strip().lower()
    if from_csv == 'y':
        csv_filename = input("Enter the CSV filename containing your ticket lines: ").strip()
        user_lines = read_user_lines_from_csv(csv_filename, game)
        if not user_lines:
            print("No valid ticket lines read from CSV. Aborting.")
            return
    else:
        lines_count = get_integer_input("How many lines do you have on your ticket? ")
        if lines_count <= 0:
            print("Number of lines must be greater than 0.")
            return

        user_lines = []
        print("\nEnter your lines:")
        for i in range(lines_count):
            while True:
                print(f"\n--- Line {i+1} ---")
                user_main = get_unique_numbers("Main number", main_count)
                user_supp = []
    
                if user_supp_count > 0:
                    user_supp = get_unique_numbers("Supplementary number", user_supp_count)
    
                # Display entered numbers for confirmation
                if user_supp_count > 0:
                    print(f"\nYou entered:")
                    print(f"Main Numbers: {', '.join(map(str, user_main))}")
                    print(f"Supplementary Numbers: {', '.join(map(str, user_supp))}")
                else:
                    print(f"\nYou entered:")
                    print(f"Main Numbers: {', '.join(map(str, user_main))}")
    
                # Ask for confirmation
                confirm = input("Is this correct? (y/n): ").strip().lower()
                if confirm == 'y':
                    user_lines.append({
                        "main": user_main,
                        "supp": user_supp
                    })
                    break
                elif confirm == 'n':
                    print("Let's re-enter the numbers for this line.")
                else:
                    print("Please enter 'y' for yes or 'n' for no.")
    
    # Ask for winning numbers
    print("\nEnter the winning numbers:")
    winning_main = get_unique_numbers("Winning main number", main_count)
    winning_supp = []
    if supp_count > 0:
        winning_supp = get_unique_numbers("Winning supplementary number", supp_count)
    
    # Tally matches
    match_counter = Counter()
    
    print("\nResults for each line:")
    for i, line in enumerate(user_lines, start=1):
        main_matches = len(set(line["main"]).intersection(winning_main))
        supp_matches = 0
        if user_supp_count > 0:
            supp_matches = len(set(line["supp"]).intersection(winning_supp))
            print(f"Line {i}: {main_matches} main matches, {supp_matches} supplementary matches")
            match_counter[(main_matches, supp_matches)] += 1
        elif supp_count > 0:
            # For games like Saturday Lotto where user does not pick supp numbers
            supp_matches = len(set(line["main"]).intersection(winning_supp))
            print(f"Line {i}: {main_matches} main matches, {supp_matches} supplementary matches")
            match_counter[(main_matches, supp_matches)] += 1
        else:
            print(f"Line {i}: {main_matches} main matches")
            match_counter[(main_matches, 0)] += 1
    
    # Print summary
    print("\nSummary of matches across all lines:")
    if user_supp_count > 0 or supp_count > 0:
        for (m_matches, s_matches), count in sorted(match_counter.items()):
            print(f"{count} ticket(s) had {m_matches} main matches and {s_matches} supplementary matches")
    else:
        for (m_matches, _), count in sorted(match_counter.items()):
            print(f"{count} ticket(s) had {m_matches} main matches")

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
    supp_count = game["supp_count"]
    user_supp_count = game["user_supp_count"]
    
    # Load historical data
    main_numbers, supp_numbers = load_historical_data(game["file"], main_count, supp_count)
    if not main_numbers:
        print("No main numbers loaded. Check CSV formatting.")
        return
    
    main_frequency = Counter(main_numbers)
    main_sorted = [num for num, freq in main_frequency.most_common()]
    main_weights = [main_frequency[num] for num in main_sorted]
    
    supp_sorted = []
    supp_weights = []
    if supp_count > 0 and supp_numbers:
        supp_frequency = Counter(supp_numbers)
        supp_sorted = [num for num, freq in supp_frequency.most_common()]
        supp_weights = [supp_frequency[num] for num in supp_sorted]
    
    lines_to_generate = get_integer_input("How many lines would you like to generate based on historical frequency? ")
    if lines_to_generate <= 0:
        print("Number of lines must be greater than 0.")
        return

    # Check if deterministic mode is feasible
    if lines_to_generate > 0:
        max_main_lines = len(main_sorted) // main_count
        max_supp_lines = len(supp_sorted) // supp_count if supp_count > 0 else float('inf')
        max_possible_lines = min(max_main_lines, max_supp_lines)
    else:
        max_possible_lines = 0

    while True:
        deterministic_input = input("Use deterministic selection (select top frequency numbers without repetition)? (y/n): ").strip().lower()
        if deterministic_input in ['y', 'n']:
            deterministic = (deterministic_input == 'y')
            break
        else:
            print("Please enter 'y' or 'n'.")

    if deterministic and lines_to_generate > max_possible_lines:
        print(f"Cannot generate {lines_to_generate} lines without repeating numbers.")
        print(f"Maximum lines that can be generated without repetition: {max_possible_lines}")
        return

    # Generate lines
    lines = generate_lines(
        main_count=main_count,
        supp_count=supp_count,
        pool_main=main_sorted,
        pool_supp=supp_sorted,
        lines_to_generate=lines_to_generate,
        main_weights=main_weights,
        supp_weights=supp_weights,
        deterministic=deterministic
    )
    
    if lines:
        print(f"\nGenerated {lines_to_generate} lines for {game['name']} based on frequency:")
        for idx, (m, s) in enumerate(lines, start=1):
            if supp_count > 0:
                print(f"Line {idx}: Main - {m}, Supp - {s}")
            else:
                print(f"Line {idx}: Main - {m}")
        
        # Option to save to CSV
        save_csv = input("Do you want to save these lines to lines.csv? (y/n): ").strip().lower()
        if save_csv == 'y':
            with open("lines.csv", "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                if supp_count > 0 and user_supp_count > 0:
                    writer.writerow(["Line #", "Main Numbers", "Supplementary Numbers"])
                    for idx, (m, s) in enumerate(lines, start=1):
                        main_str = " ".join(map(str, m))
                        supp_str = " ".join(map(str, s))
                        writer.writerow([idx, main_str, supp_str])
                elif supp_count > 0 and user_supp_count == 0:
                    # For games like Saturday Lotto where user does not pick supp numbers
                    writer.writerow(["Line #", "Main Numbers"])
                    for idx, (m, _) in enumerate(lines, start=1):
                        main_str = " ".join(map(str, m))
                        writer.writerow([idx, main_str])
                else:
                    writer.writerow(["Line #", "Main Numbers"])
                    for idx, (m, _) in enumerate(lines, start=1):
                        main_str = " ".join(map(str, m))
                        writer.writerow([idx, main_str])
            print("Lines saved to lines.csv.")
    else:
        print("No lines were generated due to insufficient data.")

def frequency_view_mode(games):
    print("Choose a game to view frequency:")
    for key, g in games.items():
        print(f"{key}. {g['name']}")
    choice = input("Enter the number of the game: ").strip()
    
    if choice not in games:
        print("Invalid choice.")
        return
    
    game = games[choice]
    main_count = game["main_count"]
    supp_count = game["supp_count"]
    
    main_numbers, supp_numbers = load_historical_data(game["file"], main_count, supp_count)
    if not main_numbers:
        print("No data loaded. Check CSV formatting.")
        return
    
    main_frequency = Counter(main_numbers)
    num_draws = len(main_numbers) // main_count
    print(f"\nFrequency of main numbers for {game['name']}:")
    for num, freq in main_frequency.most_common():
        percentage = (freq / num_draws) * 100
        print(f"Number {num}: drawn in {freq}/{num_draws} draws = {percentage:.2f}%")
    
    if supp_count > 0 and supp_numbers:
        supp_frequency = Counter(supp_numbers)
        num_draws_supp = len(supp_numbers) // supp_count
        print(f"\nFrequency of supplementary numbers for {game['name']}:")
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
            "supp_count": 2,
            "user_supp_count": 0  # Users do not pick supplementary numbers
        },
        "2": {
            "name": "Oz Lotto",
            "file": "oz-lotto.csv",
            "main_count": 7,
            "supp_count": 3,
            "user_supp_count": 3  # Users pick supplementary numbers
        },
        "3": {
            "name": "Powerball",
            "file": "powerball.csv",
            "main_count": 7,
            "supp_count": 1,
            "user_supp_count": 1  # Users pick supplementary numbers (Powerball)
        },
        "4": {
            "name": "Set for Life",
            "file": "set-for-life.csv",
            "main_count": 7,
            "supp_count": 2,
            "user_supp_count": 2  # Users pick supplementary numbers
        }
    }
    
    while True:
        print("\nDo you want to:")
        print("1. Check your ticket against winning numbers")
        print("2. Generate numbers for an upcoming game based on historical frequency")
        print("3. View frequency of each number for a chosen game")
        print("4. Exit")
        mode = input("Enter 1, 2, 3, or 4: ").strip()
        
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
