print("Rectangle suesaa calculator.\n")

io.write("Enter first number: ")
local n1 = io.read("*n")
io.write("Enter second number: ")
local n2 = io.read("*n")

while (n1 < 0 or n2 < 0)
do
    print()
    print("Please try again.")
    io.write("Enter first number: ")
    n1 = io.read("*n")
    io.write("Enter second number: ")
    n2 = io.read("*n")
end

print(n1*n2)