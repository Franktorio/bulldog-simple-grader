with open("sales.txt") as salesfile:
    lines = salesfile.readlines()

months = ["January", "February", "March", "April", "May", "June", "July",
          "August", "September", "October", "November", "December"]
month_sales = [0]*12

top_sales = 0
top_location = ""
bottom_sales = 10000000000
bottom_location = ""

for line in lines:
    data = line.split(" ")
    total_loc_sales = 0
    for i in range(12):
        total_loc_sales += int(data[i+1])
        month_sales[i] += int(data[i+1])
    if total_loc_sales >= top_sales:
        top_sales = total_loc_sales
        top_location = data[0]
    if total_loc_sales <= bottom_sales:
        bottom_sales = total_loc_sales
        bottom_location = data[0]

with open("summary.txt", "w") as summary:
    for i in range(12):
        summary.write(months[i] + " " + str(month_sales[i]) + "\n")
    summary.write("Highest sales: " + top_location + " " + str(top_sales) + "\n")
    summary.write("Lowest sales: " + bottom_location + " " + str(bottom_sales))
        
        
    
    
