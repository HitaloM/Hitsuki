class NotEnoughRights(Exception):
    def __init__(self, right):
        super(NotEnoughRights, self).__init__(right)

        self.errors = right
