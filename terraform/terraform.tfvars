db_password            = "Gigantic@!"
grafana_admin_password = "G!g@nt1c"



2. **Environment Variables:** Prefix them with `TF_VAR_`.
```bash
export TF_VAR_db_password="yourpassword"

```


3. **GitHub Secrets:** For your CI/CD pipeline, you will add these as Secrets and pass them in your YAML:
```yaml


```



---

### Pro-Tip: The `outputs.tf` file

To make these modules talk to each other (e.g., passing the VPC ID to the EKS module), you’ll also need an `outputs.tf`.

**Would you like me to provide the `outputs.tf` so your modules connect automatically without manual intervention?**