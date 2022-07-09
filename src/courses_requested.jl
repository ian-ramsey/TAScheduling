using CSV, DataFrames

opt_params = DataFrame(CSV.File("optimization_parameters.csv"));

if "directory" in opt_params.parameter
    ind = findfirst(opt_params.parameter .== "directory");
    directory = opt_params.value[ind];
    cd(directory);
else
    error("Please provide a directory");
end

course_dataset = DataFrame(CSV.File("course_dataset.csv"));
TA_dataset = DataFrame(CSV.File("TA_dataset.csv"));

## DATA PROCESSING for COURSES
number = Array{String}(course_dataset[:,"course_number"]);
days = Array{Union{Missing, String}}(course_dataset[ :,"days1"]);
times = Array{Union{Missing, String}}(course_dataset[:,"times1"]);
days2 = Array{Union{Missing, String}}(course_dataset[ :,"days2"]);
times2 = Array{Union{Missing, String}}(course_dataset[:,"times2"]);
TA_assigned = Array{Union{Missing, String}}(course_dataset[:,"ta_assigned"]);
TA_needed = Array{Bool}(course_dataset[:,"ta_needed"]);

function nolater(x::AbstractString,y::AbstractString)
# returns 1 if x is no later than x; 0 otherwise
    xP = (x[end] == 'P');  # 1 if x is PM; 0 otherwise
    yP = (y[end] == 'P');  # 1 if y is PM; 0 otherwise
    if xP < yP
        return true;
    elseif xP > yP
        return false;
    end
    xh,xm = parse.(Int, split(x[1:end-1],":"));
    yh,ym = parse.(Int, split(y[1:end-1],":"));
    # when x = 12:aa PM
    if xP && yP
        if xh == 12
            return (yh == 12) ? (xm <= ym) : true;
        else
            if yh == 12
                return false;
            end
        end
    end
    if xh < yh
        return true;
    elseif xh > yh
        return false;
    else
        return (xm <= ym);
    end
end

slot = ["7:30A" "7:59A";   "8:00A" "8:29A";
         "8:30A" "8:59A";   "9:00A" "9:29A";
         "9:30A" "9:59A";   "10:00A" "10:29A";
         "10:30A" "10:59A"; "11:00A" "11:29A";
         "11:30A" "11:59A"; "12:00P" "12:29P";
         "12:30P" "12:59P"; "1:00P" "1:29P";
         "1:30P" "1:59P";   "2:00P" "2:29P";
         "2:30P" "2:59P";   "3:00P" "3:29P";
         "3:30P" "3:59P";   "4:00P" "4:29P";
         "4:30P" "4:59P";   "5:00P" "5:29P";
         "5:30P" "5:59P";   "6:00P" "6:29P";
         "6:30P" "6:59P";   "7:00P" "7:29P";
         "7:30P" "7:59P";   "8:00P" "8:29P"];

N = length(number);  # number of all courses
TA_courses = findall(TA_needed .& ismissing.(TA_assigned));
n = length(TA_courses);
s = size(slot,1);    # number of 30-min blocks
code = String[];
section = String[];
for k = 1:N
    push!(code, number[k][1:9]);
    push!(section, number[k][11:14]);
end

grad_courses = findall("MATH:5000" .<= code);
courses_of_interest = union(TA_courses,grad_courses);

start_time = missings(String, N);
end_time = missings(String, N);
H = zeros(Bool,N,s);  # Boolean matrix for course hours
for k in courses_of_interest
    if !ismissing(times[k])
        start_time[k] = split(times[k]," - ")[1];
        end_time[k] = split(times[k]," - ")[2];
        for t = 1:s
            H[k,t] = (nolater(start_time[k],slot[t,1]) &&
                            nolater(slot[t,1],end_time[k])) ||
                     (nolater(slot[t,1],start_time[k]) &&
                            nolater(start_time[k],slot[t,2]));
        end
    end
end

# Boolean matrix for course days
D = zeros(Bool,N,5);
for k in courses_of_interest
    if ismissing(days[k])
        continue
    end
    D[k,1] = ('M' in days[k]);
    D[k,2] = ('T' in days[k]) && !('h' in days[k]);
    D[k,3] = ('W' in days[k]);
    D[k,4] = ('h' in days[k]);
    D[k,5] = ('F' in days[k]);
    if contains(days[k],"TT") || contains(days[k],"TWT")
        D[k,2] = true;
    end
end

# Binary array for times of courses
T = zeros(Bool,N,5,s);
for k = 1:N
    for d = 1:5
        for t = 1:s
            T[k,d,t] = D[k,d] && H[k,t];
        end
    end
end

# For courses with two different times
courses_with_multiple_times = findall(.!ismissing.(times2));
if length(courses_with_multiple_times) > 0
    for k in courses_with_multiple_times
        d_bool = zeros(Bool,5);
        d_bool[1] = ('M' in days2[k]);
        d_bool[2] = ('T' in days2[k]) && !('h' in days2[k]);
        d_bool[3] = ('W' in days2[k]);
        d_bool[4] = ('h' in days2[k]);
        d_bool[5] = ('F' in days2[k]);
        if contains(days2[k],"TT") || contains(days2[k],"TWT")
            d_bool[2] = true;
        end
        d = findall(d_bool);
        t_start = split(times2[k]," - ")[1];
        t_end = split(times2[k]," - ")[2];
        for t = 1:s
            T[k,d,t] .|= (nolater(t_start,slot[t,1]) && nolater(slot[t,1],t_end)) ||
                        (nolater(slot[t,1],t_start) && nolater(t_start,slot[t,2]));
        end
    end
end

# FROM NOW ON, INDEXES of COURSES ARE DIFFERENT
# TA[new_index] = old_index

# List of courses
course_list = unique(code);
sections_of = Dict{String,Array{Int64,1}}()
for course in course_list
    push!(sections_of, course => findall(code[TA_courses] .== course));
end
TA_course_codes = unique(code[TA_courses]);

## DATA PROCESSING for TA DATASET
TA_name = Array{String}(TA_dataset[:,"name"]);
year = Array{Int64}(TA_dataset[:,"year_in_program"]);
course_pref1 = Array{Union{Missing, String}}(TA_dataset[:,"1_course_pref"]);
course_pref2 = Array{Union{Missing, String}}(TA_dataset[:,"2_course_pref"]);
course_pref3 = Array{Union{Missing, String}}(TA_dataset[:,"3_course_pref"]);
course_pref4 = Array{Union{Missing, String}}(TA_dataset[:,"4_course_pref"]);
course_pref5 = Array{Union{Missing, String}}(TA_dataset[:,"5_course_pref"]);
unavail_days_0730_0820 = Array{Union{Missing, String}}(TA_dataset[:,"07:30_08:20_unavail_days"]);
unavail_days_0830_0920 = Array{Union{Missing, String}}(TA_dataset[:,"08:30_09:20_unavail_days"]);
unavail_days_0930_1020 = Array{Union{Missing, String}}(TA_dataset[:,"09:30_10:20_unavail_days"]);
unavail_days_1030_1120 = Array{Union{Missing, String}}(TA_dataset[:,"10:30_11:20_unavail_days"]);
unavail_days_1100_1150 = Array{Union{Missing, String}}(TA_dataset[:,"11:00_11:50_unavail_days"]);
unavail_days_1130_1220 = Array{Union{Missing, String}}(TA_dataset[:,"11:30_12:20_unavail_days"]);
unavail_days_1230_1320 = Array{Union{Missing, String}}(TA_dataset[:,"12:30_13:20_unavail_days"]);
unavail_days_1330_1420 = Array{Union{Missing, String}}(TA_dataset[:,"13:30_14:20_unavail_days"]);
unavail_days_1400_1450 = Array{Union{Missing, String}}(TA_dataset[:,"14:00_14:50_unavail_days"]);
unavail_days_1430_1520 = Array{Union{Missing, String}}(TA_dataset[:,"14:30_15:20_unavail_days"]);
unavail_days_1530_1620 = Array{Union{Missing, String}}(TA_dataset[:,"15:30_16:20_unavail_days"]);
unavail_days_1630_2359 = Array{Union{Missing, String}}(TA_dataset[:,"16:30_23:59_unavail_days"]);
TA_math_courses = Array{Union{Missing, String}}(TA_dataset[:,"gradmath_courses"]);

m = length(TA_name);

# Course preferences of TAs
course_pref = Matrix{Union{Missing, String}}(undef,m,5);
for j = 1:m
    course_pref[j,1] = ismissing(course_pref1[j]) ? missing : course_pref1[j][1:9];
    course_pref[j,2] = ismissing(course_pref2[j]) ? missing : course_pref2[j][1:9];
    course_pref[j,3] = ismissing(course_pref3[j]) ? missing : course_pref3[j][1:9];
    course_pref[j,4] = ismissing(course_pref4[j]) ? missing : course_pref4[j][1:9];
    course_pref[j,5] = ismissing(course_pref5[j]) ? missing : course_pref5[j][1:9];
end

# Availability of TAs
S = [[1,2],   # 7:30A-7:59A and 8:00A-8:29A
     [3,4],   # 8:30A-8:59A and 9:00A-9:29A
     [5,6],   # 9:30A-9:59A and 10:00A-10:29A
     [7,8],   # 10:30A-10:59A and 11:00A-11:29A
     [8,9],   # 11:00A-11:29A and 11:30A-11:59A
     [9,10],  # 11:30A-11:59A and 12:00P-12:29P
     [11,12], # 12:30P-12:59P and 1:00P-1:29P
     [13,14], # 1:30P-1:59P and 2:00P-2:29P
     [14,15], # 2:00P-2:29P and 2:30P-2:59P
     [15,16], # 2:30P-2:59P and 3:00P-3:29P
     [17,18], # 3:30P-3:59P and 4:00P-4:29P
     collect(19:s) # 4:30P-later
    ];

unavail_days = [unavail_days_0730_0820,
                unavail_days_0830_0920,
                unavail_days_0930_1020,
                unavail_days_1030_1120,
                unavail_days_1100_1150,
                unavail_days_1130_1220,
                unavail_days_1230_1320,
                unavail_days_1330_1420,
                unavail_days_1400_1450,
                unavail_days_1430_1520,
                unavail_days_1530_1620,
                unavail_days_1630_2359];

available = ones(Bool,m,5,s);
for j = 1:m
    for t = 1:length(S)
        if ismissing(unavail_days[t][j])
            continue
        end
        d = Int[];
        if occursin("Monday",unavail_days[t][j])
            append!(d,1);
        end
        if occursin("Tuesday",unavail_days[t][j])
            append!(d,2);
        end
        if occursin("Wednesday",unavail_days[t][j])
            append!(d,3);
        end
        if occursin("Thursday",unavail_days[t][j])
            append!(d,4);
        end
        if occursin("Friday",unavail_days[t][j])
            append!(d,5);
        end
        available[j,d,S[t]] .= 0;
    end
end

# Make sure TAs are unavailable when they are in MATH courses
for j = 1:m
    if ismissing(TA_math_courses[j])
        continue
    end
    for k in grad_courses
        if occursin(code[k],TA_math_courses[j])
            available[j,:,:] .&= .!T[k,:,:];
        end
    end
end

# Make sure first-year students are unavailable during the first-year seminar
index_5900 = findfirst(code .== "MATH:5900");
if index_5900 != nothing
    for j = 1:m
        if year[j] == 1
            available[j,:,:] .&= .!T[index_5900,:,:];
        end
    end
end

# Availability of TA j for course k: [j,k]
A = zeros(Bool,m,n);
for j = 1:m
    for k = 1:n
        A[j,k] = !(0 in available[j,findall(T[TA_courses[k],:,:])]);
    end
end

## PREPARE courses_requested.csv
n_codes = length(TA_course_codes);
courses_requested = zeros(Int,n_codes,m);
for j = 1:m
    if any(ismissing.(course_pref[j,:]))
        continue
    end
    for c = 1:n_codes
        course = TA_course_codes[c];
        if course in course_pref[j,:]
            courses_requested[c,j] = findfirst(course .== course_pref[j,:]);
        end
    end
end

course_numbers = String[];
TA_names = String[];
years = Int[];
ranks = Int[];
availability = Int[];
for c = 1:n_codes
    course = TA_course_codes[c];
    J = findall(courses_requested[c,:] .> 0);
    rank = courses_requested[c,J];
    if length(J) == 0
        continue
    end
    for k in sections_of[course]
        # List TAs preferring the course
        for i = 1:length(J)
            j = J[i];
            push!(course_numbers, number[TA_courses[k]]);
            push!(TA_names, TA_name[j]);
            push!(years, year[j]);
            push!(ranks, rank[i]);
            push!(availability, A[j,k]);
        end
        # List all available TAs for the course
        for j in setdiff(1:m,J)
            if A[j,k]
                push!(course_numbers, number[TA_courses[k]]);
                push!(TA_names, TA_name[j]);
                push!(years, year[j]);
                push!(ranks, 0);
                push!(availability, 1);
            end
        end
    end
end

result = [course_numbers TA_names years ranks availability];
df = DataFrame(result, [:course_number, :TA_name, :TA_year, :TA_preference, :TA_available]);
CSV.write("courses_requested.csv",df)
