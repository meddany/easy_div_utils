from .utils import getRandomKey
from .custom_env import custom_env , setupEnvironment 

env = custom_env()


def getEventEmitter( id ) :
    '''
    When EventEmitter is called or initialized it automatically is stored in memory with certain id.
    you can call this event from memory by passing that id to this function which will return the event if found.
    if not.. it will return None
    '''
    ev = env.get('event_emitter' , {} )
    return ev.get( id , None )


# This script defines an EventEmitter class, which is a basic implementation of the event emitter pattern in Python.
# The event emitter is designed to manage events and associated callbacks in an application.

class EventEmitter:
    def __init__(self, id=getRandomKey(n=15)):
        """
        Initializes an EventEmitter instance.

        Parameters:
        - id: Unique identifier for the event emitter. Defaults to a random key of length 15.
        """
        self.listeners = {}  # Dictionary to store event listeners
        self.id = id  # Unique identifier for the event emitter
          # Global environment to store event emitters
        
        setupEnvironment( 'event_emitter' )

        env['event_emitter'][id] = self  # Register the event emitter in the global environment
        self.env = env['event_emitter'][id]  # Reference to the event emitter in the global environment

    def isEventSubscribed(self, event):
        if event in list(self.listeners.keys()) :
            return True
        return False

    def addEventListener(self, event, callback):
        """
        Adds an event listener for the specified event.

        Parameters:
        - event: Name of the event.
        - callback: Callback function to be executed when the event is triggered.
        """
        if event not in self.listeners:
            self.listeners[event] = []  # Create an entry for the event if it doesn't exist
        self.listeners[event].append(callback)  # Add the callback to the list of event listeners

    def removeEventListener(self, event, callback):
        """
        Removes a specified callback function from the list of event listeners for the given event.

        Parameters:
        - event: Name of the event.
        - callback: Callback function to be removed.
        """
        if event in self.listeners:
            self.listeners[event].remove(callback)  # Remove the callback if it exists

    def dispatchEvent(self, event):
        """
        Triggers the specified event, executing all associated callback functions.

        Parameters:
        - event: Name of the event to be triggered.
        """
        if event in self.listeners:
            for callback in self.listeners[event]:
                callback()  # Execute each callback associated with the event

# Example of usage:
if __name__ == '__main__':
    pass  # Placeholder statement, does nothing
