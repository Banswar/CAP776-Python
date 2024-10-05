import csv
import re
import bcrypt
import requests
import time
import random
import os
import getpass
from datetime import datetime

USERS_FILE = 'users.csv'
HISTORY_FILE = 'search_history.csv'

def initializeCsvFiles():
    if not os.path.exists(USERS_FILE):
        with open(USERS_FILE, 'w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(['email', 'password_hash', 'security_question', 'security_answer'])
    
    if not os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, 'w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(['timestamp', 'email', 'search_term', 'selected_game'])

def loadUsers():
    usersDict = {}
    try:
        with open(USERS_FILE, mode='r', newline='') as file:
            reader = csv.DictReader(file)
            for row in reader:
                usersDict[row['email']] = {
                    'password_hash': row['password_hash'].encode('utf-8'),
                    'security_question': row['security_question'],
                    'security_answer': row['security_answer']
                }
    except FileNotFoundError:
        pass
    return usersDict

def saveUsers(usersDict):
    with open(USERS_FILE, mode='w', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=['email', 'password_hash', 'security_question', 'security_answer'])
        writer.writeheader()
        for email, data in usersDict.items():
            writer.writerow({
                'email': email,
                'password_hash': data['password_hash'].decode('utf-8'),
                'security_question': data['security_question'],
                'security_answer': data['security_answer']
            })

def validateEmail(email):
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))

def validatePassword(password):
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    if not re.search(r'[A-Z]', password):
        return False, "Password must contain at least one uppercase letter"
    if not re.search(r'[a-z]', password):
        return False, "Password must contain at least one lowercase letter"
    if not re.search(r'\d', password):
        return False, "Password must contain at least one number"
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        return False, "Password must contain at least one special character"
    return True, "Password meets all requirements"

def generateCaptcha():
    num1 = random.randint(1, 10)
    num2 = random.randint(1, 10)
    operator = random.choice(['+', '-', '*'])
    
    if operator == '+':
        answer = num1 + num2
    elif operator == '-':
        answer = num1 - num2
    else:
        answer = num1 * num2
    
    question = f"What is {num1} {operator} {num2}? "
    return question, str(answer)

def verifyCaptcha():
    question, correctAnswer = generateCaptcha()
    userAnswer = input(question)
    return userAnswer == correctAnswer

def searchGame(gameTitle):
    try:
        params = {'title': gameTitle, 'limit': 5}
        response = requests.get("https://www.cheapshark.com/api/1.0/games", params=params)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"Error searching for game: {e}")
        return []

def getGameDeals(gameId):
    try:
        params = {'id': gameId}
        response = requests.get("https://www.cheapshark.com/api/1.0/games", params=params)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"Error fetching game details: {e}")
        return None

def getStoreNames():
    try:
        response = requests.get("https://www.cheapshark.com/api/1.0/stores")
        if response.status_code == 200:
            stores = response.json()
            return {str(store['storeID']): store['storeName'] for store in stores}
        return {}
    except requests.RequestException:
        return {}

def addToHistory(email, searchTerm, selectedGame=None):
    with open(HISTORY_FILE, 'a', newline='') as file:
        writer = csv.writer(file)
        writer.writerow([datetime.now(), email, searchTerm, selectedGame])

def getUserHistory(email):
    history = []
    try:
        with open(HISTORY_FILE, 'r', newline='') as file:
            reader = csv.reader(file)
            next(reader)
            for row in reader:
                if len(row) >= 4 and row[1] == email:
                    history.append({
                        'timestamp': row[0],
                        'search_term': row[2],
                        'selected_game': row[3]
                    })
    except FileNotFoundError:
        pass
    return history

def clearScreen():
    os.system('cls' if os.name == 'nt' else 'clear')

def displayMenu():
    clearScreen()
    print("\n1. Login")
    print("2. Register")
    print("3. Forgot Password")
    print("4. Exit")
    return input("Enter your choice (1-4): ")

def registerUser(usersDict):
    email = input("Enter email: ")
    if not validateEmail(email):
        print("Invalid email format")
        return
    
    if email in usersDict:
        print("Email already registered")
        return
    
    password = getpass.getpass("Enter password: ")
    passwordConfirm = getpass.getpass("Confirm password: ")
    
    if password != passwordConfirm:
        print("Passwords do not match!")
        return
    
    isValid, message = validatePassword(password)
    if not isValid:
        print(message)
        return
    
    securityQuestion = input("Enter security question: ")
    securityAnswer = input("Enter security answer: ")
    
    passwordHash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    usersDict[email] = {
        'password_hash': passwordHash,
        'security_question': securityQuestion,
        'security_answer': securityAnswer
    }
    saveUsers(usersDict)
    print("Registration successful")

def loginUser(usersDict):
    email = input("Enter email: ")
    if email not in usersDict:
        print("Email not found")
        return None
    
    if not verifyCaptcha():
        print("CAPTCHA verification failed")
        return None
    
    password = getpass.getpass("Enter password: ")
    userData = usersDict[email]
    
    if bcrypt.checkpw(password.encode('utf-8'), userData['password_hash']):
        print("Login successful")
        return email
    else:
        print("Invalid password")
        return None

def resetPassword(usersDict):
    email = input("Enter email: ")
    if email not in usersDict:
        print("Email not found")
        return
    
    userData = usersDict[email]
    print(f"Security Question: {userData['security_question']}")
    answer = input("Enter security answer: ")
    
    if answer.lower() != userData['security_answer'].lower():
        print("Incorrect security answer")
        return
    
    newPassword = getpass.getpass("Enter new password: ")
    confirmPassword = getpass.getpass("Confirm new password: ")
    
    if newPassword != confirmPassword:
        print("Passwords do not match!")
        return
    
    isValid, message = validatePassword(newPassword)
    if not isValid:
        print(message)
        return
    
    userData['password_hash'] = bcrypt.hashpw(newPassword.encode('utf-8'), bcrypt.gensalt())
    saveUsers(usersDict)
    print("Password reset successful")

def displayGameDetails(gameId, storeNames):
    gameDetails = getGameDeals(gameId)
    if gameDetails and 'deals' in gameDetails:
        print(f"\nGame: {gameDetails['info']['title']}")
        for deal in gameDetails['deals']:
            storeName = storeNames.get(deal['storeID'], f"Store {deal['storeID']}")
            print(f"\nStore: {storeName}")
            print(f"Price: ${deal['price']}")
            print(f"Retail Price: ${deal['retailPrice']}")
            
            if 'savings' in deal:
                try:
                    savings = float(deal['savings'])
                    print(f"Savings: {savings:.2f}%")
                except ValueError:
                    print("Savings: Not available")
            
            time.sleep(0.1)
    else:
        print("Could not fetch game details.")

def gameSearchMenu(currentUser, storeNames):
    while True:
        clearScreen()
        print(f"\nLogged in as: {currentUser}")
        print("\n1. Search for games")
        print("2. View search history")
        print("3. Logout")
        
        choice = input("Enter your choice (1-3): ")
        
        if choice == '1':
            gameTitle = input("\nEnter game title to search: ")
            addToHistory(currentUser, gameTitle)
            
            games = searchGame(gameTitle)
            if not games:
                print("No games found.")
                input("\nPress Enter to continue...")
                continue
            
            print("\nFound games:")
            for i, game in enumerate(games, 1):
                print(f"{i}. {game['external']}")
            
            try:
                gameChoice = int(input("Select a game (enter number): ")) - 1
                if 0 <= gameChoice < len(games):
                    selectedGame = games[gameChoice]['external']
                    addToHistory(currentUser, None, selectedGame)
                    displayGameDetails(games[gameChoice]['gameID'], storeNames)
                else:
                    print("Invalid selection.")
            except ValueError:
                print("Please enter a valid number.")
            input("\nPress Enter to continue...")
        
        elif choice == '2':
            history = getUserHistory(currentUser)
            if history:
                print("\nYour search history:")
                for item in history:
                    print(f"Time: {item['timestamp']}")
                    if item['search_term']:
                        print(f"Searched: {item['search_term']}")
                    if item['selected_game']:
                        print(f"Selected: {item['selected_game']}")
                    print("---")
            else:
                print("\nNo search history found.")
            input("\nPress Enter to continue...")
        
        elif choice == '3':
            break
        
        else:
            print("Invalid choice. Please try again.")
            input("\nPress Enter to continue...")

def main():
    initializeCsvFiles()
    usersDict = loadUsers()
    storeNames = getStoreNames()
    
    while True:
        choice = displayMenu()
        
        if choice == '1':
            currentUser = loginUser(usersDict)
            if currentUser:
                gameSearchMenu(currentUser, storeNames)
        elif choice == '2':
            registerUser(usersDict)
            input("\nPress Enter to continue...")
        elif choice == '3':
            resetPassword(usersDict)
            input("\nPress Enter to continue...")
        elif choice == '4':
            print("Goodbye!")
            break
        else:
            print("Invalid choice. Please try again.")
            input("\nPress Enter to continue...")

if __name__ == "__main__":
    main()