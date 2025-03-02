# BasketballPlayerCard Component

## Description

This is a React component that displays information about a basketball player, including their name, image, position, and stats (points per game, assists per game, and rebounds per game).

## Installation

1. Clone the repository:
    ```bash
    git clone https://github.com/Obiorachibuike/BasketBallCard.git
    ```
2. Navigate to the project directory:
    ```bash
    cd BasketBallCard
    ```
3. Install the dependencies:
    ```bash
    npm install
    ```

## Usage

1. Start the development server:
    ```bash
    npm start
    ```
2. Open your browser and go to `http://localhost:3000`.

## Component Props

- `name` (string): The player's name.
- `image` (string): URL to the player's image.
- `position` (string): The player's position.
- `stats` (object): An object containing the player's stats (e.g., { pointsPerGame: 25.4, assistsPerGame: 7.1, reboundsPerGame: 10.5 }).

## Example

```jsx
<BasketballPlayerCard
  name="LeBron James"
  image="https://example.com/lebron.jpg"
  position="Forward"
  stats={{ pointsPerGame: 25.4, assistsPerGame: 7.1, reboundsPerGame: 10.5 }}
/>
 #   B a s k e t B a l l C a r d  
 