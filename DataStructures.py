class CircularQueue:
    def __init__(self, size):
        """
        CIRCULAR QUEUE
        - front points to the first element
        - rear points to the last element
        - when queue is empty: front = rear = -1
        """

        self.size = size
        self.queue = [None] * size  # Fixed-size list 
        self.front = -1             # Index of front element
        self.rear = -1              # Index of rear element

    def enqueue(self, item):
        """
        ADDS AN ITEM TO THE REAR OF THE QUEUE

        - Checks if queue is full before inserting
        - Wraps around using modulo when reaching end of list
        """

        # Condition for full queue (next position of rear is front)
        if (self.rear + 1) % self.size == self.front:
            print("ERROR: Queue is full")
            return

        # If queue is empty, initialise front and rear
        if self.front == -1:
            self.front = 0
            self.rear = 0
        else:
            # Move rear forward in circularly
            self.rear = (self.rear + 1) % self.size

        # Insert the new item
        self.queue[self.rear] = item

    def dequeue(self):
        """
        REMOVES AND RETURNS THE FRONT ITEM FROM THE QUEUE

        - Checks if queue is empty
        - Resets queue when last element is removed
        """

        # Queue is empty
        if self.front == -1:
            print("ERROR: Queue is empty")
            return None

        # Retrieve the front item
        item = self.queue[self.front]

        # If only one element was present, reset queue
        if self.front == self.rear:
            self.front = -1
            self.rear = -1
        else:
            # Move front forward circularly
            self.front = (self.front + 1) % self.size

        return item

    def displayQueue(self):
        """
        DISPLAYS ALL ELEMENTS IN THE QUEUE FROM FRONT TO REAR

        - Iterates from front to rear
        - Wraps around using modulo if needed
        - NOT USED IN ACTUAL CODE JUST TEST
        """

        # Queue is empty
        if self.front == -1:
            print("Queue is empty")
            return

        i = self.front

        # Traverse circularly until reaching rear
        while True:
            print(self.queue[i], end=" ")
            if i == self.rear:
                break
            i = (i + 1) % self.size

        print()