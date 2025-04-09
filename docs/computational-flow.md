
```mermaid
flowchart TD
    subgraph Microscope_Computer
        style Microscope_Computer fill:#ffccff,stroke:#333,stroke-width:2px
        microscope_computer[Computer with Microscope] --> B[new volume]
    end

    subgraph Jumphost
        style Jumphost fill:#cceeff,stroke:#333,stroke-width:2px
        microscope_computer <-->|local Network| jumphost[Jumphost]
        jumphost --> docker_container[docker container]

        subgraph Docker Container
            style Docker_Container fill:#ccffcc,stroke:#333,stroke-width:2px
            docker_container --> E[check if folder in log]
            E -->|True| F[check if size > log size]
            E -->|False| G[compress]
            F -->|False| I[skip]
            F -->|True| G
            G --> H[extract Metadata]
            B --> H
            
        end

        subgraph Globus
            style Globus fill:#ffccff,stroke:#333,stroke-width:2px
            H --> globus[Globus DataTransfer]
            G --> globus[Globus DataTransfer]
            
        end
    end

    subgraph DataFed_API
        globus --> repo[DataFed Repository]
        style DataFed_API fill:#ffffcc,stroke:#333,stroke-width:2px
        H --> datafed1[DataFed dataCreate Command]
        H --> G
        repo --> datafed1
        G --> datafed2[DataFed dataPut Command]
        datafed1 --> datafed2[DataFed dataPut Command]
    end

    subgraph View Details
    task[task id]
    progress[task progress]
    datafed2 --> progress 
    progress --> task 
    end
```
