import random
import uuid
from typing import List, Dict, Any
from dataclasses import dataclass, asdict

@dataclass
class Shape:
    id: str
    shape_type: str
    color: str
    x: int
    y: int
    size: int
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

class ShapesManager:
    ALLOWED_SHAPES = ['triangle', 'circle', 'rectangle']
    ALLOWED_COLORS = ['red', 'blue', 'yellow', 'green']
    CANVAS_SIZE = 800
    
    def __init__(self):
        self.shapes: List[Shape] = []
        self.user_shapes: Dict[int, List[Shape]] = {}  # user_id -> shapes
    
    def initialize_for_user(self, user_id: int, preferences: List[Dict[str, Any]]) -> List[Shape]:
        """Initialize canvas with user's favorite shapes"""
        self.user_shapes[user_id] = []
        
        if preferences:
            # Draw favorite shapes based on user history
            for pref in preferences[:10]:  # Limit to 10 shapes
                for _ in range(min(pref['count'], 3)):  # Max 3 of each type
                    shape = Shape(
                        id=str(uuid.uuid4()),
                        shape_type=pref['shape_type'],
                        color=pref['color'],
                        x=random.randint(50, self.CANVAS_SIZE - 50),
                        y=random.randint(50, self.CANVAS_SIZE - 50),
                        size=random.randint(20, 80)
                    )
                    self.user_shapes[user_id].append(shape)
        else:
            # First time user - random shapes
            self._initialize_random_shapes(user_id)
        
        return self.user_shapes[user_id]
    
    def _initialize_random_shapes(self, user_id: int):
        """Create random initial shapes for new users"""
        num_shapes = random.randint(5, 10)
        for _ in range(num_shapes):
            shape = Shape(
                id=str(uuid.uuid4()),
                shape_type=random.choice(self.ALLOWED_SHAPES),
                color=random.choice(self.ALLOWED_COLORS),
                x=random.randint(50, self.CANVAS_SIZE - 50),
                y=random.randint(50, self.CANVAS_SIZE - 50),
                size=random.randint(20, 80)
            )
            self.user_shapes[user_id].append(shape)
    
    def get_shapes(self, user_id: int) -> List[Dict[str, Any]]:
        """Get shapes for specific user"""
        if user_id not in self.user_shapes:
            return []
        return [shape.to_dict() for shape in self.user_shapes[user_id]]
    
    def add_shape(self, user_id: int, shape_type: str, color: str, 
                  x: int = None, y: int = None, size: int = 50) -> bool:
        """Add shape for specific user"""
        if shape_type not in self.ALLOWED_SHAPES or color not in self.ALLOWED_COLORS:
            return False
        
        if user_id not in self.user_shapes:
            self.user_shapes[user_id] = []
        
        if x is None:
            x = random.randint(50, self.CANVAS_SIZE - 50)
        if y is None:
            y = random.randint(50, self.CANVAS_SIZE - 50)
        
        shape = Shape(
            id=str(uuid.uuid4()),
            shape_type=shape_type,
            color=color,
            x=x,
            y=y,
            size=size
        )
        self.user_shapes[user_id].append(shape)
        return True
    
    def remove_shape(self, user_id: int, shape_type: str, color: str) -> bool:
        """Remove shape for specific user"""
        if user_id not in self.user_shapes:
            return False
        
        for i, shape in enumerate(self.user_shapes[user_id]):
            if shape.shape_type == shape_type and shape.color == color:
                self.user_shapes[user_id].pop(i)
                return True
        return False
    
    def resize_shape(self, user_id: int, shape_type: str, color: str, size_change: int) -> bool:
        """Resize shape for specific user"""
        if user_id not in self.user_shapes:
            return False
        
        for shape in self.user_shapes[user_id]:
            if shape.shape_type == shape_type and shape.color == color:
                shape.size = max(10, min(200, shape.size + size_change))
                return True
        return False
    
    def clear_shapes(self, user_id: int):
        """Clear shapes for specific user"""
        self.user_shapes[user_id] = []
        self._initialize_random_shapes(user_id)
    
    def get_shape_count(self, user_id: int, shape_type: str = None, color: str = None) -> int:
        """Count shapes for user with optional filters"""
        if user_id not in self.user_shapes:
            return 0
        
        count = 0
        for shape in self.user_shapes[user_id]:
            if shape_type and shape.shape_type != shape_type:
                continue
            if color and shape.color != color:
                continue
            count += 1
        return count
