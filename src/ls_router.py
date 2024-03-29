# Base router class
from router import Router

# This is long enough so that broadcasts complete even on large topologies
BROADCAST_INTERVAL = 1000


# Class representing link state routers
class LSRouter(Router):
    def __init__(self, router_id, clock):
        # Common initialization routines
        Router.__init__(self, router_id, clock)

        # Is the broadcast complete? => Can we run Dijkstra's algorithm?
        # For now, we'll use a simple heuristic for this:
        # If BROADCAST_INTERVAL since the first link state advertisement (LSA) at time 0,
        # we'll declare the broadcast complete
        self.broadcast_complete = False

        # Have you run Dijkstra's algorithm? This is to ensure you don't repeatedly run it.
        self.routes_computed = False

        # LSA dictionary mapping from a router ID to the links for that router.
        # We'll initialize lsa_dict to  this router's own links.
        self.lsa_dict = dict()

        # For each LSA received from a distinct router,
        # maintain if it has been broadcasted or not.
        # This is to avoid repeated broadcasts of the same LSA
        # We'll initialize self.broadcasted to reflect the fact that this router's own links
        # have not yet been broadcasted as of time 0.
        self.broadcasted = {self.router_id: False}

    # Initialize link state to this router's own links alone
    def initialize_algorithm(self):
        self.lsa_dict = {self.router_id: self.links}

    def run_one_tick(self):
        if self.clock.read_tick() >= BROADCAST_INTERVAL and not self.routes_computed:
            # If broadcast phase is over, compute routes and return
            self.broadcast_complete = True
            self.dijkstras_algorithm()
            self.routes_computed = True
            return
        elif self.clock.read_tick() < BROADCAST_INTERVAL:
            # TODO: Go through the LSAs received so far.
            # broadcast each LSA to this router's neighbors if the LSA has not been broadcasted yet

            #lsa_dict is a table of router IDs mapping to advertisements
            for router, ad in self.lsa_dict.items():
                # If we have not broadcasted or we are looking at a router who's ad has not been broadcasted,
                # then we broadcast the ad and the router it came from
                if not router in self.broadcasted.keys() or self.broadcasted[router] == False:
                    # broadcast each previously unbroadcasted ad to all neighbors
                    for neighbor in self.neighbors:
                        self.send(neighbor, ad, router)
                    # after sending to all neighbors, mark that ad as broadcasted
                    self.broadcasted[router] = True
            
            pass
        else:
            return

    # Note that adv_router is the router that generated this advertisement,
    # which may be different from "self",
    # the router that is broadcasting this advertisement by sending it to a neighbor of self.
    def send(self, neighbor, ls_adv, adv_router):
        neighbor.lsa_dict[adv_router] = ls_adv
        # It's OK to reinitialize this even if adv_router even if adv_router is in lsa_dict

    def dijkstras_algorithm(self):
        # TODO:
        # (1) Implement Dijkstra's single-source shortest path algorithm
        # to find the shortest paths from this router to all other destinations in the network.
        # Feel free to use a different shortest path algo. if you're more comfortable with it.
        # (2) Remember to populate self.fwd_table with the next hop for every destination
        # because simulator.py uses this to check your LS implementation.
        # (3) If it helps, you can use the helper function next_hop below to compute the next hop once you
        # have populated the prev dictionary which maps a destination to the penultimate hop
        # on the shortest path to this destination from this router.

        # initialize set of not visited routers with all routers in lsa_dict because we haven't started,
        # so none are visited yet
        not_visited = set(self.lsa_dict.keys())

        # initialize distances as infinity (for min comparisons)
        # initialize prev as -1 for all routers to show that none are connected as part of the shortest path yet
        distances = {}
        prev = {} 
        for router in self.lsa_dict.keys():
            distances[router] = float('inf')
            prev[router] = -1
        # initialize distance to self as 0
        distances[self.router_id] = 0


        # Dijkstra's algorithm iterates until not_visited is empty, 
        # in other words until all routers have been visited
        while not_visited:
            # Find the router with the minimum distance
            min_distance = float('inf')
            min_router = None

            # Initially this will be self because all others are infinity, 
            # next round will be min edge from self to one of its neighbors, etc.
            for router in not_visited:
                if distances[router] < min_distance:
                    min_distance = distances[router]
                    min_router = router
            

            
            # mark the minimum distance router as visited
            not_visited.remove(min_router)
            
            # update distances to neighbors of min_router by checking if going through min_router is shorter
            for neighbor, cost in self.lsa_dict[min_router].items():
                if neighbor in not_visited:
                    # new distance to router x is distance to min router + distance from min router to router x
                    new_distance = distances[min_router] + cost
                    # only update with new distance if it less than old distance
                    if new_distance < distances[neighbor]:
                        distances[neighbor] = new_distance
                        prev[neighbor] = min_router
        
        # populate forwarding table using prev dictionary 
        # and the recursive next_hop function
        for router in self.lsa_dict.keys():
            if router != self.router_id and prev[router]] != -1:
                next_hop_router = self.next_hop(router, prev)
                self.fwd_table[router] = next_hop_router

        # set routes_computed as True after visiting all routers and updating forwarding table for all routers
        self.routes_computed = True

        pass

    # Recursive function for computing next hops using the prev dictionary
    def next_hop(self, dst, prev):
        # Can't find next_hop if dst is disconnected from self.router_id
        assert prev[dst] != -1
        # Nor if dst and self.router_id are the same
        assert self.router_id != dst
        if prev[dst] == self.router_id:
            # base case, src and dst are directly connected
            return dst
        else:
            return self.next_hop(prev[dst], prev)
