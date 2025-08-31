# Deterministic Physics Simulation - Image Reveal

This project implements a **deterministic 2D physics simulation** where multiple balls move, collide, and bounce off boundaries, eventually revealing an uploaded image as their colors map to the pixels of the image.

---

## Features

- **Deterministic Physics Engine:** Uses Verlet integration for accurate motion simulation.
- **Gravity & Collisions:** Balls are affected by gravity, bounce off walls, and collide with each other.
- **Image Reveal:** Balls take colors from an uploaded image, forming a near pixel-perfect representation over time.
- **Optimized Collision Handling:** Uses spatial hashing to reduce computational overhead for collisions.
- **CSV-based Ball Tracking:** Ball positions and states are recorded in `ball_spawns.csv` for deterministic replay.
- **Customizable Parameters:** Easily adjust gravity, ball radius, spawn rate, number of objects, and simulation steps.
- **Fast Calculation Phase:** Precomputes ball positions for smooth real-time display.

---

## Requirements

- Python 3.10+  
- [Pygame](https://www.pygame.org/)  
- [Pillow (PIL)](https://pillow.readthedocs.io/en/stable/)  
- Tkinter (for image file selection, usually included with Python)

Install required packages:
**pip install pygame pillow**
