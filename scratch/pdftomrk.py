
                for page_num, page in enumerate(pdf.pages, start=1):
                    tables = page.extract_tables()
                    for tbl in tables:
                        if tbl and any(any(cell for cell in row) for row in tbl):
                            df = pd.DataFrame(tbl)
                  df["page"] = page_n
                            all_tables.append(df)

                if all_tables:
                    full = pd.concat(all_tables, ignore_index=True)
                    full.to_csv(csv_path, index=False)
                    log(f"   ✅ Tables extracted ({len(all_tables)} tables)")
                else:
                    log("   ℹ️ No tables found")
        except Exception as e:
            log(f"   ⚠️ Table extraction error: {e}")

    except Exception as e:
        log(f"❌ Fatal error on {fname}: {e}")

log("🏁 Batch conversion finished")
