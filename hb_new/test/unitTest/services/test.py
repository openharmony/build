import sys 
class StatusCode():
    
    def __init__(self, status=True, info=''):
        self.status = status
        self.info = info
        

def check_status(func):
    status = func()
    if not status.status:
        raise Exception("hhhhhhhhhhh")
    return StatusCode

A_CONST = 1

@check_status
def func_1() -> StatusCode:
    if A_CONST == 1:
        return StatusCode()
    else:
        return StatusCode(False, "error")
# func_1 = check_status(func_1)

def main():
    func_1()
    print(func_1)

if __name__ == "__main__":
    sys.exit(main())
