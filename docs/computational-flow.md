
```mermaid
flowchart TD
    subgraph Microscope Computer
        style Microscope Computer fill:#ffccff,stroke:#333,stroke-width:2px
        microscope_computer[Computer with Microscope] -->B[new volume]
    end
    subgraph Jumphost
        style Jumphost fill:#cceeff,stroke:#333,stroke-width:2px
        microscope_computer <-->|local Network| jumphost[Jumphost]
        jumphost --> docker_container[docker container]
        subgraph Docker Container
            style Docker Container fill:#ccffcc,stroke:#333,stroke-width:2px
            docker_container[ls volume get folders size] --> E[check if folder in log]
            E[check if folder in log]-->|True|F[check if size > log size]
            E[check if folder in log]-->|False|G[compress]
            F[check if size > log size]-->|False|I[skip]
            F[check if size > log size]-->|True|G[compress]
            G --> H[extract Metadata]
            B --> H[extract Metadata]
        end
end
subgraph DataFed API
    style DataFed API fill:#ffffcc,stroke:#333,stroke-width:2px
    H --> datafed1[DataFed dataCreate Command]
    G[compress] --> datafed2[DataFed dataPut Command]
end
