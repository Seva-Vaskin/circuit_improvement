#!/bin/bash

usage() {
    echo "Usage: $0 number_of_inputs number_of_outputs time_limit basis result_directory pred_directory [--circuit_size SIZE]"
    echo "  number_of_inputs: An integer representing the number of inputs"
    echo "  number_of_outputs: An integer representing the number of outputs"
    echo "  time_limit: An integer representing maximum searching time for one circuit"
    echo "  basis: BENCH/AIG"
    echo "  result_directory: The directory to store the results"
    echo "  pred_directory: The directory to store number of gates predictions"
    echo "  --circuit_size: Optional argument to specify the circuit size"
    exit 1
}

validate_integer() {
    local re='^[0-9]+$'
    for var in "$@"; do
        if ! [[ $var =~ $re ]]; then
            echo "Error: Expected an integer. Got: $var"
            usage
            return 1 # Return error
        fi
    done
}

parse_arguments() {
    # Initialize optional arguments with default values if necessary
    circuit_size="0"
    # Parse arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            --circuit_size)
                circuit_size="$2"
                shift # past argument
                shift # past value
                ;;
            *) # preserve positional arguments
                positional_args+=("$1")
                shift # past argument
                ;;
        esac
    done

    # Restore positional parameters
    set -- "${positional_args[@]}"

    # Check if exactly six arguments are provided (excluding the optional --circuit_size)
    if [ "${#positional_args[@]}" -ne 6 ]; then
        echo "Error: Incorrect number of arguments. Got (${#positional_args[@]})"
        usage
    fi

    number_of_inputs=$1
    number_of_outputs=$2
    time_limit=$3
    basis=$4
    result_directory=$5
    pred_directory=$6
}

join_by() {
    local IFS="$1"     # Set the separator
    shift               # Shift the arguments, $2 becomes $1, $3 becomes $2, etc.
    echo "$*"          # Echo the joined array elements
}

create_directory() {
    local dir_name=$1

    # Check if the directory already exists
    if [ -d "$dir_name" ]; then
        # Ask the user for permission to override
        read -p "Directory '$dir_name' exists. Is it ok? Should we continue? (y/n): " answer

        case $answer in
            [Yy]* )
                echo "Continue working with the existing directory '$dir_name'."
                ;;
            [Nn]* )
                echo "Exit."
                exit 1
                ;;
            * )
                echo "Invalid input :("
                exit 1
                ;;
        esac
    else
        # Create the directory if it doesn't exist
        mkdir "$dir_name"
        echo "Directory '$dir_name' created."
    fi
}

format_time() {
    local total_seconds=$1
    local hours
    local minutes
    local seconds

    hours=$(echo "$total_seconds / 3600" | bc)
    minutes=$(echo "($total_seconds % 3600) / 60" | bc)
    seconds=$(echo "$total_seconds % 60" | bc)

    integer_seconds=$(printf "%.0f" "$seconds")  # Round to nearest integer

    printf "%02d:%02d:%02d\n" "$hours" "$minutes" "$integer_seconds"
}


update_running_pids() {
    for i in "${!running_pids[@]}"; do
        pid=${running_pids[$i]}
        # Delete finished
        if ! kill -0 "$pid" 2>/dev/null; then
            # Check the exit status
            wait "${pid}"
            if [ -$? -ne 0 ]; then
                ((killed_counter++))
            fi

            # Process is no longer running, remove it
            unset 'running_pids[i]'
        fi
    done
}

MAX_RUNNING_PROCESSES=16
UPDATE_TIMEOUT=1

main() {
    parse_arguments "$@"
    validate_integer "$number_of_inputs" "$number_of_outputs" "$time_limit"
    if [ $? -ne 0 ]; then
        echo "Validation failed."
        exit 1
    fi

    cd "$(dirname "$0")" || exit

    create_directory "$pred_directory"
    create_directory "$result_directory"

    echo "Loading functions..."
    mapfile -t truth_tables < <(python ./generate_all_functions.py "$number_of_inputs" "$number_of_outputs" "$basis")
    echo "Loaded ${#truth_tables[@]} functions"

    ulimit -t "${time_limit}"

    declare -a running_pids
    killed_counter=0
    start_time=$(date +%s)
    interval=100
    total_iterations=${#truth_tables[@]}
    counter=0
    echo "Start search"
    for tables in "${truth_tables[@]}"; do
        eval "python ./find_circuit.py --circuit_size ${circuit_size} ${number_of_inputs} ${basis} ${pred_directory} ${result_directory} ${tables[*]}" &
        pid=$!
        running_pids+=("$pid")

        if [[ ${#running_pids[@]} -ge $MAX_RUNNING_PROCESSES ]]; then
            update_running_pids
        fi

        if [[ ${#running_pids[@]} -ge $MAX_RUNNING_PROCESSES ]]; then
            while [[ ${#running_pids[@]} -ge $MAX_RUNNING_PROCESSES ]] ; do
                sleep $UPDATE_TIMEOUT
                update_running_pids
            done
        fi

        ((counter++))
        if (( counter % interval == 0 )); then
            current_time=$(date +%s)
            elapsed_time=$((current_time - start_time))
            average_time_per_iteration=$(echo "$elapsed_time / $counter" | bc -l)
            estimated_total_time=$(echo "$average_time_per_iteration * $total_iterations" | bc -l)

            echo "[$(date '+%Y-%m-%d %H:%M:%S')] Iteration $counter/$total_iterations. Elapsed: $(format_time $elapsed_time), estimated total: $(format_time "$estimated_total_time")"
        fi
    done

    echo "Started all tasks! Wait till finish!"
    while [[ ${#running_pids[@]} -gt 0 ]] ; do
        sleep $UPDATE_TIMEOUT
        update_running_pids
    done
    echo "All done"
    if [ "$killed_counter" -gt 0 ]; then
        echo "Didn't manage to find circuits for ${killed_counter}/${total_iterations} functions"
    else
        echo "All ${total_iterations} functions are found"
    fi
}

main "$@"