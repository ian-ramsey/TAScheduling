## LOAD PACKAGES, SET DIRECTORY and GET OPTIMIZATION PARAMETERS
using CSV, DataFrames
opt_params = DataFrame(CSV.File("optimization_parameters.csv"));

if "directory" in opt_params.parameter
    dir_index = findfirst(opt_params.parameter .== "directory");
    directory = opt_params.value[dir_index];
    cd(directory);
else
    error("Please provide a directory");
end
if "workload_id" in opt_params.parameter
    id_index = findfirst(opt_params.parameter .== "workload_id");
    workload_id = parse(Int,opt_params.value[id_index]);
else
    workload_id = 1;
end

## DATA PROCESSING for COURSES
course_dataset = DataFrame(CSV.File("course_dataset.csv"));

number = Array{String}(course_dataset[:,"course_number"]);
course_name = Array{String}(course_dataset[:,"course_name"]);
supervisor = Array{Union{Missing, String}}(course_dataset[:,"course_supervisor(s)"]);
days = Array{Union{Missing, String}}(course_dataset[ :,"days1"]);
times = Array{Union{Missing, String}}(course_dataset[:,"times1"]);
days2 = Array{Union{Missing, String}}(course_dataset[ :,"days2"]);
times2 = Array{Union{Missing, String}}(course_dataset[:,"times2"]);
TA_assigned = Array{Union{Missing, String}}(course_dataset[:,"ta_assigned"]);
TA_needed = Array{Bool}(course_dataset[:,"ta_needed"]);
workload = Array{Union{Missing, Real}}(course_dataset[:,"workload_$(workload_id)"]);


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

# Clusters of times
early_morning = collect(1:4);
morning = collect(5:9);
early_afternoon = collect(10:14);
afternoon = collect(15:18);
evening = collect(19:26);

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
first_year_courses = findall("MATH:5000" .<= code .< "MATH:6000");
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

# Binary matrix for conflicts of courses
conflict = zeros(Bool,n,n);
for k = 1:n
    for l = 1:n
        if sum(T[TA_courses[k],:,:] .* T[TA_courses[l],:,:]) > 0
            conflict[k,l] = true;
        end
    end
end

# Time clusters of courses
dummy = zeros(Bool,n,5);
for k = 1:n
    k_start = minimum(findall(H[TA_courses[k],:]));
    dummy[k,1] = k_start in early_morning;
    dummy[k,2] = k_start in morning;
    dummy[k,3] = k_start in early_afternoon;
    dummy[k,4] = k_start in afternoon;
    dummy[k,5] = k_start in evening;
end
cluster = Array{Int64,1}[];
for i = 1:5
    push!(cluster, findall(dummy[:,i]));
end

# List of courses
course_list = unique(code);
sections_of = Dict{String,Array{Int64,1}}()
for course in course_list
    push!(sections_of, course => findall(code[TA_courses] .== course));
end

TA_course_codes = unique(code[TA_courses]);
number_of_sections_of = Dict{String,Int64}()
sections_of_course = Array{Int64,1}[];
for course in TA_course_codes
    push!(number_of_sections_of, course => length(sections_of[course]));
    push!(sections_of_course, sections_of[course]);
end
number_of_sections_of_standalone = number_of_sections_of["MATH:0100"] +
                                   number_of_sections_of["MATH:1005"] +
                                   number_of_sections_of["MATH:1010"] +
                                   number_of_sections_of["MATH:1020"];
n_course = length(TA_course_codes);  # number of courses

# Same courses
same_course = zeros(Bool,n,n);
for k = 1:n
    for l = 1:n
        same_course[k,l] = (code[TA_courses[k]] == code[TA_courses[l]]);
    end
end

# Workload of courses
if any(ismissing.(workload[TA_courses]))
    error("Missing workload data");
else
    w = Array{Float64}(workload[TA_courses]);
end

# Section grouping for courses with workload < 1
easy_sections = findall(workload[TA_courses] .< 1);
easy_courses = unique(code[TA_courses[easy_sections]]);
group_index = Int[];
for course in easy_courses
    ind = findfirst(TA_course_codes .== course);   # check this!
    if length(sections_of_course[ind]) > 1
        append!(group_index, ind);
    end
end
# group = sections_of_course[group_index];

# Section grouping for instructors
subgroup = Array{Int64,1}[];
TA_sections = section[TA_courses];
for course in easy_courses
    I = findall((code .== course) .& (TA_needed .== false));  # old indexes of supervisors
    J = sections_of[course];  # new indexes of TAs
    Sup = unique(supervisor[I]);
    if length(Sup) > 1
        for sup in Sup
            subJ = Int[];
            for i in I
                if sup == supervisor[i]
                    for s = section[i]
                        if isletter(s)
                            j = intersect(J,findall(occursin.(s,TA_sections)));
                            append!(subJ,j);
                        end
                    end
                end
            end
            unique!(subJ);
            sort!(subJ);
            push!(subgroup,subJ);
        end
    end
end
n_subgroup = length(subgroup);

# Standalone courses
standalone_courses = union(sections_of["MATH:0100"],
                           sections_of["MATH:1005"],
                           sections_of["MATH:1010"],
                           sections_of["MATH:1020"]);

# Light courses (1350, 1440, 1460, 1550) for 1st-year students
light_courses = union(sections_of["MATH:1350"],
                      sections_of["MATH:1440"],
                      sections_of["MATH:1460"],
                      sections_of["MATH:1550"]);

# Hard courses (3000 and higher, and standalone courses)
hard_course_codes = ["MATH:0100","MATH:1005","MATH:1010","MATH:1020"];
append!(hard_course_codes, unique(code[findall("MATH:3000" .<= code)]));

hard_courses = Int[];
for course in hard_course_codes
    append!(hard_courses, sections_of[course]);
end

## DATA PROCESSING for TA DATASET
TA_dataset = DataFrame(CSV.File("TA_dataset.csv"));
TA_name = Array{String}(TA_dataset[:,"name"]);
TA_email = Array{Union{Missing, String}}(TA_dataset[:,"email"]);
assignment = Array{Union{Missing, String}}(TA_dataset[:,"assignment"]);
TA_year = Array{Int64}(TA_dataset[:,"year_in_program"]);
standalone_taught = Array{Union{Missing, String}}(TA_dataset[:,"hard_courses_taught"]);
time_pref_early_morning = Array{Union{Missing, Int64}}(TA_dataset[:,"07:30_09:30_pref"]);
time_pref_morning = Array{Union{Missing, Int64}}(TA_dataset[:,"09:30_11:30_pref"]);
time_pref_early_afternoon = Array{Union{Missing, Int64}}(TA_dataset[:,"12:00_14:00_pref"]);
time_pref_afternoon = Array{Union{Missing, Int64}}(TA_dataset[:,"14:00_16:00_pref"]);
time_pref_evening = Array{Union{Missing, Int64}}(TA_dataset[:,"16:00_23:59_pref"]);
course_pref1 = Array{Union{Missing, String}}(TA_dataset[:,"1_course_pref"]);
course_pref2 = Array{Union{Missing, String}}(TA_dataset[:,"2_course_pref"]);
course_pref3 = Array{Union{Missing, String}}(TA_dataset[:,"3_course_pref"]);
course_pref4 = Array{Union{Missing, String}}(TA_dataset[:,"4_course_pref"]);
course_pref5 = Array{Union{Missing, String}}(TA_dataset[:,"5_course_pref"]);
time_course_pref = Array{Union{Missing, String}}(TA_dataset[:,"time_course_pref"]);
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
TA_other_courses = Array{Union{Missing, String}}(TA_dataset[:,"other_courses"]);
overload = Array{Union{Missing, String}}(TA_dataset[:,"overload"]);
mathlab_or_grading = Array{Union{Missing, String}}(TA_dataset[:,"mathlab_or_grading"]);

M = length(TA_name);
# indexes of TAs to be part of TA assignment
TA = findall(ismissing.(assignment));
m = length(TA);

year = TA_year[TA];
first_year_TAs = findall(year .== 1);
higher_year_TAs = setdiff(1:m,first_year_TAs);  # 2nd year or higher

# Standalone courses taught by TAs
standalone = zeros(Bool,m);  # 1 if they have not taught standalone
taught_0100 = zeros(Bool,m);
taught_1005 = zeros(Bool,m);
taught_1010 = zeros(Bool,m);
taught_1020 = zeros(Bool,m);
taught_1560 = zeros(Bool,m);
for j = 1:m
    i = TA[j];
    if ismissing(standalone_taught[i])
        standalone[j] = 1;
    elseif year[j] == 1
        standalone[j] = 1;
    else
        standalone[j] = occursin("I have not taught any of these", standalone_taught[i]);
        taught_0100[j] = occursin("0100", standalone_taught[i]);
        taught_1005[j] = occursin("1005", standalone_taught[i]);
        taught_1010[j] = occursin("1010", standalone_taught[i]);
        taught_1020[j] = occursin("1020", standalone_taught[i]);
        taught_1560[j] = occursin("1560", standalone_taught[i]);
    end
end


# Time preferences of TAs
time_pref = hcat(time_pref_early_morning[TA],
                 time_pref_morning[TA],
                 time_pref_early_afternoon[TA],
                 time_pref_afternoon[TA],
                 time_pref_evening[TA]);

# Course preferences of TAs
course_pref = Matrix{Union{Missing, String}}(undef,m,5);
for j = 1:m
    i = TA[j];
    course_pref[j,1] = ismissing(course_pref1[i]) ? missing : course_pref1[i][1:9];
    course_pref[j,2] = ismissing(course_pref2[i]) ? missing : course_pref2[i][1:9];
    course_pref[j,3] = ismissing(course_pref3[i]) ? missing : course_pref3[i][1:9];
    course_pref[j,4] = ismissing(course_pref4[i]) ? missing : course_pref4[i][1:9];
    course_pref[j,5] = ismissing(course_pref5[i]) ? missing : course_pref5[i][1:9];
end

# number_of_TA_prefered[k] = the number of TAs preferred course k
number_of_TA_prefered = Dict{String,Int64}();
for course in TA_course_codes
    num = 0;
    for j = 1:m
        if !any(ismissing.(course_pref[j,:]))
            num += (course in course_pref[j,:]);
        end
    end
    push!(number_of_TA_prefered, course => num);
end

# Number of TAs who prefer standalone courses except 1st-year students
TA_pref_standalone = Int[];  # check this
for j in higher_year_TAs
    if any(ismissing.(course_pref[j,:]))
        continue
    end
    if (("MATH:0100" in course_pref[j,:]) || ("MATH:1005" in course_pref[j,:]) ||
        ("MATH:1010" in course_pref[j,:]) || ("MATH:1020" in course_pref[j,:]))
        append!(TA_pref_standalone,j);
    end
end
pref_standalone = length(TA_pref_standalone);

# Time-course preference coefficient
r = zeros(m);  # weight for course preferences
for j = 1:m
    i = TA[j];
    if ismissing(time_course_pref[i])
        r[j] = 2/4;
    elseif occursin("Time",time_course_pref[i])
        r[j] = 1/4;
    elseif occursin("equal",time_course_pref[i])
        r[j] = 2/4;
    elseif occursin("Course",time_course_pref[i])
        r[j] = 3/4;
    end
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

unavail_days = [unavail_days_0730_0820[TA],
                unavail_days_0830_0920[TA],
                unavail_days_0930_1020[TA],
                unavail_days_1030_1120[TA],
                unavail_days_1100_1150[TA],
                unavail_days_1130_1220[TA],
                unavail_days_1230_1320[TA],
                unavail_days_1330_1420[TA],
                unavail_days_1400_1450[TA],
                unavail_days_1430_1520[TA],
                unavail_days_1530_1620[TA],
                unavail_days_1630_2359[TA]];


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
available_first = copy(available);

# Make sure TAs are unavailable when they are in MATH courses
for j = 1:m
    i = TA[j];
    if ismissing(TA_math_courses[i])
        continue
    end
    for k in grad_courses
        if occursin(code[k],TA_math_courses[i])
            available[j,:,:] .&= .!T[k,:,:];
        end
    end
end
available_second = copy(available);

# Make sure first-year students are unavailable during the first-year seminar
index_5900 = findfirst(code .== "MATH:5900");
if index_5900 == nothing  # For Spring
    for j = 1:m
        if year[j] == 1
            available[j,5,17:18] .= 0;  # Friday 3:30P - 4:20P
        end
    end
else  # For Fall
    for j = 1:m
        if year[j] == 1
            available[j,:,:] .&= .!T[index_5900,:,:];
        end
    end
end

# If 1st-year student is unavailable for 9 or less slots,
# make them unavailable for all MWF and discussion sections of 1st-year courses
for j = 1:m
    if (year[j] == 1) && (sum(available[j,:,:] .== 0) < 10)
        available[j,[1,3,5],:] .= 0;
        for k in first_year_courses
            available[j,:,:] .&= .!T[k,:,:];
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

#=
for j = 1:m
    println(available_first[j,:,:] == available_second[j,:,:])
end
=#

## CONSTRUCT THE MODEL
using JuMP, Gurobi, Statistics

# Model parameters
α = [8,7,6,5,4];
β = [8,6,4,2,0];
θ = [3,4,6,3];
φ = [8,4];

# Course coefficients
p_course = zeros(m,n);
# For first-year students
for j in first_year_TAs
    if any(ismissing.(course_pref[j,:]))
        p_course[j,light_courses] .= θ[3];
    else
        for p = 1:5
            if course_pref[j,p] in hard_course_codes
                continue
            else
                p_course[j,sections_of[course_pref[j,p]]] .= α[p];
            end
        end
        p_course[j,light_courses] .+= θ[3];
    end
end
# For second-year or higher students
for j in higher_year_TAs
    if any(ismissing.(course_pref[j,:]))
        p_course[j,:] .= θ[1];
    else
        for p = 1:5
            p_course[j,sections_of[course_pref[j,p]]] .= α[p];
        end
    end
end

# Time coefficients
time_coeff = zeros(Int,m,5);
for j = 1:m
    for t = 1:5
        if ismissing(time_pref[j,t])
            time_coeff[j,t] = θ[2];
        else
            time_coeff[j,t] = β[time_pref[j,t]];
        end
    end
end
p_time = zeros(m,n);
for j = 1:m
    for t = 1:5
        p_time[j,cluster[t]] .= time_coeff[j,t];
    end
end

# Weighted average of course and time coefficients
p = zeros(m,n);  # coefficients for the decision variables
for j = 1:m
    p[j,:] = r[j] * p_course[j,:] + (1-r[j]) * p_time[j,:];
end

# If third-year or higher TA has not taught any standalone courses
if pref_standalone < number_of_sections_of_standalone
    for j = 1:m
        if (year[j] > 2) && standalone[j]
            p[j,standalone_courses] .+= θ[4];
        end
    end
end

# Initialize the model
model = Model(Gurobi.Optimizer);
# Define decision variables
@variable(model, x[1:m,1:n], binary=true);
@variable(model, u[1:n], binary=true);
@variable(model, y[1:m,1:n_course], binary=true);
@variable(model, z[1:m,1:n_course] >=0, integer=true);
@variable(model, ys[1:m,1:n_subgroup], binary=true);
@variable(model, zs[1:m,1:n_subgroup] >=0, integer=true);
# Set the objective
@objective(model, Max, sum(p[j,k]*x[j,k] for j=1:m, k=1:n)
                        + φ[1] * sum(z[j,c] for j=1:m, c=group_index)
                        + φ[2] * sum(zs[j,i] for j=1:m, i=1:n_subgroup)
                        - 1000 * sum(u[k] for k=1:n));

for k = 1:n
    # Each section has at most one TA assigned to it:
    @constraint(model, u[k] + sum(x[j,k] for j=1:m) == 1);
    for j = 1:m
        # TA availability for sections
        @constraint(model, x[j,k] <= A[j,k]);
        # TAs cannot be assigned to any overlapping courses:
        @constraint(model, sum(conflict[k,l]*x[j,l] for l=1:n) <= 1);
    end
end
for j = 1:m
    # No TA can be overloaded
    @constraint(model, sum(w[k]*x[j,k] for k=1:n) <= 1);
end
for j = 1:m
    # Grouping
    for c = 1:n_course
        @constraint(model, sum(x[j,k] for k in sections_of_course[c]) == y[j,c] + z[j,c]);
        @constraint(model, z[j,c] <= 4 * y[j,c]);
    end
    # Subgrouping
    for i = 1:n_subgroup
        @constraint(model, sum(x[j,k] for k in subgroup[i]) >= ys[j,i] + zs[j,i]);
        @constraint(model, zs[j,i] <= 4 * ys[j,i]);
    end
end
# Do not assign 3 sections from two different courses
for j = 1:m
    @constraint(model, sum(4*y[j,c]+z[j,c] for c=1:n_course) <= 8);
end
# Assign no more than 2 sections to first_year TAs
for j in first_year_TAs
    @constraint(model, sum(x[j,k] for k=1:n) <= 2);
end
# Do not let 1st-year teach standalone and 3000 & higher level courses
for j in first_year_TAs
    for k in hard_courses
        @constraint(model, x[j,k] == 0);
    end
end

status = optimize!(model);
# Print results
println(termination_status(model));
println("Optimal Value: ", objective_value(model));
if sum(value(u[k]) for k=1:n) > 0.5
    println("NO FEASIBLE SOLUTION!")
else
    println("There is a feasible solution!")
end
# Results for courses
course_result = String[];
for k = 1:n
    for j = 1:m
        if value(x[j,k]) > 0.5
            #println("  x[$j,$k] = ", value.(x[j,k]));
            push!(course_result, number[TA_courses[k]] * " : " * TA_name[TA[j]]);
        end
    end
end
# Results for TAs
TA_result = Array{String,1}(undef,m);
results = Tuple{Int64,Int64}[];
for j = 1:m
    TA_result[j] = "[";
    k_num = 0;
    for k = 1:n
        if value(x[j,k]) > 0.5
            k_num += 1;
            #println("  x[$j,$k] = ", value.(x[j,k]));
            #println(TA_name[j]," : ",number[TAcourses[k]]);
            push!(results, (j,k));
            if k_num > 1
                TA_result[j] *= ", ";
            end
            TA_result[j] *= "'" * number[TA_courses[k]] * " - " * course_name[TA_courses[k]] * "'";
        end
    end
    TA_result[j] *= "]";
end

## WRITING THE ASSIGNMENT RESULTS
for (j,k) in results
    TA_assigned[TA_courses[k]] = TA_name[TA[j]];
end
course_dataset.ta_assigned = TA_assigned;
CSV.write("course_output.csv",course_dataset)

assignment[TA] = TA_result;
TA_dataset.assignment = assignment;
CSV.write("TA_output.csv",TA_dataset)


## PERFORMANCE EVALUATION
#=
prefer(j,k) = findfirst(code[TA_courses[k]] .== course_pref[j,:]);
course_pref_result = Matrix{Union{String,Int}}(undef,m,3);
for j = 1:m
    i = 1;
    for k = 1:n
        if value(x[j,k]) > 0.99
            if code[TA_courses[k]] in course_pref[j,:]
                course_pref_result[j,i] = prefer(j,k);
            else
                course_pref_result[j,i] = "not prefered";
            end
            i += 1;
        end
    end
    if i <= 3
        course_pref_result[j,i:3] .= "n/a";
    end
end
course_pref_result2 = zeros(Int,n);
for k = 1:n
    j = findfirst(value.(x[:,k]) .> 0.99);
    if j == nothing
        println("k=",k," j=",j);
        break
    end
    if code[TA_courses[k]] in course_pref[j,:]
        course_pref_result2[k] = prefer(j,k);
    end
end

for i = 0:5
    println("preference $i :",sum(course_pref_result2 .== i))
end

time_pref_result = Matrix{Union{String,Int}}(undef,m,3);
for j = 1:m
    i = 1;
    for k = 1:n
        if value(x[j,k]) > 0.99
            if k in cluster[1]
                time_pref_result[j,i] = time_pref_early_morning[j];
            elseif k in cluster[2]
                time_pref_result[j,i] = time_pref_morning[j];
            elseif k in cluster[3]
                time_pref_result[j,i] = time_pref_early_afternoon[j];
            elseif k in cluster[4]
                time_pref_result[j,i] = time_pref_afternoon[j];
            elseif k in cluster[5]
                time_pref_result[j,i] = time_pref_evening[j];
            end
            i += 1;
        end
    end
    if i <= 3
        time_pref_result[j,i:3] .= "n/a";
    end
end

time_pref_result2 = zeros(Int,n);
for k = 1:n
    j = findfirst(value.(x[:,k]) .> 0.99);
    if k in cluster[1]
        time_pref_result2[k] = time_pref_early_morning[j];
    elseif k in cluster[2]
        time_pref_result2[k] = time_pref_morning[j];
    elseif k in cluster[3]
        time_pref_result2[k] = time_pref_early_afternoon[j];
    elseif k in cluster[4]
        time_pref_result2[k] = time_pref_afternoon[j];
    elseif k in cluster[5]
        time_pref_result2[k] = time_pref_evening[j];
    end
end
for i = 1:5
    println("preference $i :",sum(time_pref_result2 .== i))
end

# TA Satisfaction
TA_satisfaction = zeros(m);
for j = 1:m
    course_sat = Int[];
    time_sat = Int[];
    for k = 1:n
        if value(x[j,k]) == 1
            if course_pref_result2[k] == 0
                append!(course_sat, 10);
            else
                append!(course_sat, course_pref_result2[k]);
            end
            append!(time_sat, time_pref_result2[k]);
        end
    end
    TA_satisfaction[j] = λ[j]*mean(course_sat) + (1-λ[j])*mean(time_sat);
end
=#
