"""نقطة الدخول — Minecraft 2D Desktop"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from minecraft2d.game import Game

def main():
    g = Game()
    g.run()

if __name__ == "__main__":
    main()
